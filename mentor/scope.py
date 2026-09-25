"""Decide which code a review covers.

Every run answers "which code should I ask you about?" first. See
context.md §36.2 for the rules this implements.
"""

from dataclasses import dataclass, field
from fnmatch import fnmatch

from mentor import git as g

# git's well-known empty tree: diffing against it shows every file as added,
# which lets "last N commits" work even when N reaches past the first commit.
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

NOISE_PATTERNS = [
  ".mentor/*",
  "*.lock",
  "package-lock.json",
  "pnpm-lock.yaml",
  "*.min.js",
  "*.min.css",
  "*.map",
]


@dataclass
class Scope:
  label: str                      # human-readable, e.g. "main..feat/x + uncommitted"
  kind: str                       # "diff" or "all"
  base: str | None = None         # commit/tree the diff is taken against
  files: list[str] = field(default_factory=list)
  untracked: list[str] = field(default_factory=list)
  stats: str = ""

  @property
  def is_empty(self):
    return not self.files and not self.untracked


def is_noise(path):
  return any(fnmatch(path, pattern) for pattern in NOISE_PATTERNS)


def exclude_pathspecs():
  return ["--", ".", *[f":(exclude){p}" for p in NOISE_PATTERNS]]


def resolve_scope(args, state, ask):
  """Pick the review scope from CLI flags, saved state, and (first run) the user.

  `ask(prompt, options)` is injected so the CLI owns all terminal I/O.
  """
  if args.all:
    return _whole_repo()

  if args.uncommitted:
    return _diff_scope(g.head_commit() or EMPTY_TREE, "uncommitted changes")

  if args.since:
    base = _resolve_since(args.since)
    start = "start" if base == EMPTY_TREE else g.short(base)
    return _diff_scope(base, f"since {args.since} ({start}) + uncommitted")

  branch = g.current_branch()
  default = args.base or g.default_branch()

  if args.base or (default and branch != default and branch != "HEAD"):
    if not default:
      raise g.GitError("No base branch found — pass --base <branch>.")
    base = g.git("merge-base", default, "HEAD").strip()
    return _diff_scope(base, f"{default}..{branch} + uncommitted")

  last = state.get("last_reviewed_commit")
  if last and g.ref_exists(last) and g.is_ancestor(last):
    return _diff_scope(last, f"since last review ({g.short(last)}) + uncommitted")

  return _first_run(ask)


def _first_run(ask):
  commit_count = int(g.git("rev-list", "--count", "HEAD").strip()) if g.head_commit() else 0
  last_n = min(5, commit_count)

  options = [("whole", "Whole project")]
  if last_n:
    options.append(("recent", f"Last {last_n} commits"))
  if g.has_uncommitted_changes():
    options.append(("uncommitted", "Only uncommitted changes"))

  choice = ask("You haven't reviewed this repo before. What should I look at?", options)

  if choice == "whole":
    return _whole_repo()
  if choice == "uncommitted":
    return _diff_scope(g.head_commit() or EMPTY_TREE, "uncommitted changes")

  base = f"HEAD~{last_n}" if last_n < commit_count else EMPTY_TREE
  base = g.git("rev-parse", base).strip() if base != EMPTY_TREE else base
  return _diff_scope(base, f"last {last_n} commits + uncommitted")


def _resolve_since(since):
  if g.ref_exists(since):
    return g.git("rev-parse", since).strip()

  # Not a commit — treat it as a date ("3 days ago", "2026-09-01").
  before = g.git("rev-list", "-1", f"--before={since}", "HEAD").strip()
  return before or EMPTY_TREE


def _diff_scope(base, label):
  files = [f for f in g.git("diff", "--name-only", base, *exclude_pathspecs()).splitlines() if f]
  untracked = [f for f in g.untracked_files() if not is_noise(f)]
  stats = g.git("diff", "--shortstat", base, *exclude_pathspecs()).strip()
  if untracked:
    stats = f"{stats}, {len(untracked)} untracked file(s)".lstrip(", ")

  return Scope(label=label, kind="diff", base=base, files=files, untracked=untracked, stats=stats)


def _whole_repo():
  files = [f for f in g.tracked_files() + g.untracked_files() if not is_noise(f)]
  return Scope(label="whole project", kind="all", files=files, stats=f"{len(files)} files")
