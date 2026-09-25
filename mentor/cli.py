import argparse
import os
import sys
from pathlib import Path

from mentor import git as g
from mentor.context import build_context
from mentor.llm import MissingAPIKey, ensure_api_key, extract_decisions
from mentor import ui
from mentor.record import DECISIONS_FILE, load_state, owned_titles, ownership, pending_decisions, save_state
from mentor.scope import resolve_scope
from mentor.session import QuitSession, read_input, run_session
from mentor.verify import filter_decisions

QUESTIONS_PER_RUN = 3

NON_CODE_SUFFIXES = {
  ".md", ".txt", ".rst", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
  ".csv", ".lock", ".svg", ".png", ".jpg", ".gif", ".ico",
}
NON_CODE_NAMES = {".gitignore", ".env.example", "LICENSE", "requirements.txt"}

OVERVIEW = f"""\
mentor — own the design decisions in code you didn't write.

Finds the design decisions in your recent changes, asks you about them,
grades your answers, and records what you understand in
.mentor/DECISIONS.md.

Usage:
  mentor review [options]

What to review (pick at most one; default is "recent changes"):
  (no option)          on a branch: changes since it split from main
                       on main: changes since your last review
  --uncommitted        only changes you haven't committed yet
  --since WHEN         since a commit (ddd39e8) or a date ("3 days ago")
  --base BRANCH        on a branch, compare against BRANCH instead of main
  --all                the whole repo
  --more               continue with decisions left from the last review

How to review:
  -n NUMBER            questions to ask (default {QUESTIONS_PER_RUN})
  -v, --verbose        show each step as it runs
  -h, --help           show this help

During a review:
  type your answer, then Enter      h  hint      e  explain
  s  skip this question             q  quit (progress is saved)

Examples:
  mentor review                     review what's new
  mentor review --uncommitted       check what Claude just wrote
  mentor review --since "2 days ago" -n 5
  mentor review --all -v
"""


class FriendlyParser(argparse.ArgumentParser):
  """argparse, but every error points at the full help screen."""

  def error(self, message):
    sys.stderr.write(f"mentor: {message}\n\nRun `mentor -h` to see every command and option.\n")
    sys.exit(2)


def main(argv=None):
  argv = sys.argv[1:] if argv is None else argv
  if not argv or argv[0] in ("-h", "--help", "help"):
    print(OVERVIEW)
    return

  parser = FriendlyParser(prog="mentor", add_help=False, allow_abbrev=False)
  sub = parser.add_subparsers(dest="command", required=True, parser_class=FriendlyParser)

  review = sub.add_parser("review", add_help=False, allow_abbrev=False)
  review.add_argument("-h", "--help", action="store_true")
  review.add_argument("--all", action="store_true", help="review the whole repo")
  review.add_argument("--uncommitted", action="store_true", help="only uncommitted changes")
  review.add_argument("--since", metavar="REF", help="changes since a commit or date ('3 days ago')")
  review.add_argument("--base", metavar="BRANCH", help="on a branch, compare against BRANCH instead of main")
  review.add_argument("--more", action="store_true", help="continue with decisions left over from the last review")
  review.add_argument("-n", type=int, default=QUESTIONS_PER_RUN, help=f"questions to ask (default {QUESTIONS_PER_RUN})")
  review.add_argument("-v", "--verbose", action="store_true", help="show each pipeline step")

  args = parser.parse_args(argv)
  if args.help:
    print(OVERVIEW)
    return

  try:
    os.chdir(g.repo_root())
  except g.GitError:
    sys.exit("mentor: not inside a git repository.")

  try:
    ensure_api_key()
    if args.more:
      review_pending(args)
    else:
      review_scope(args)
  except (g.GitError, MissingAPIKey) as error:
    sys.exit(f"mentor: {error}")


def review_scope(args):
  state = load_state()
  try:
    scope = resolve_scope(args, state, ask_choice)
  except QuitSession:
    return

  if scope.is_empty:
    ui.info(f"Nothing to review ({scope.label}).")
    return

  ui.step(args.verbose, "scope", f"{scope.label} · {len(scope.files) + len(scope.untracked)} files · {scope.stats}")

  if not any(looks_like_code(path) for path in scope.files + scope.untracked):
    ui.note("Only config/docs changed, so decisions may be shallow. `mentor review --all` looks at everything.")

  context = build_context(scope)
  source = "whole files" if scope.kind == "all" else "diff only"
  ui.step(args.verbose, "context", f"{source} · {len(context.text):,} chars")
  if context.truncated:
    ui.note("This change is large, so some files were left out. Try a narrower range (--since / --uncommitted).")

  with ui.working(f"Reading {scope.label} and finding design decisions…"):
    found = extract_decisions(context.text, scope.label, owned_titles=owned_titles(state))
  decisions, dropped = filter_decisions(found, context.visible_lines)
  ui.step(args.verbose, "decisions", f"{len(found)} found · {len(dropped)} dropped · ranked")
  for decision, reason in dropped:
    ui.step(args.verbose, "", f"  dropped “{decision.title}” — {reason}")

  state["last_reviewed_commit"] = g.head_commit()

  if not decisions:
    state["pending"] = []
    save_state(state)
    ui.info("No design decisions worth asking about in this change.")
    return

  asked = decisions[:args.n]
  ui.found(len(decisions), len(asked), scope.label)
  finish(state, asked, decisions[args.n:], scope.label)


def review_pending(args):
  state = load_state()
  pending = pending_decisions(state)
  if not pending:
    ui.info("Nothing left over from the last review. Run `mentor review` for new changes.")
    return

  ui.info(f"{len(pending)} decision(s) left from the last review.")
  finish(state, pending[:args.n], pending[args.n:], "continued review")


def finish(state, asked, remaining, scope_label):
  state["pending"] = [d.model_dump() for d in asked + remaining]
  before = ownership(state)

  tally, requeue = run_session(asked, state, scope_label)
  # skipped/unreached go after the untouched remainder so --more shows new ones first
  state["pending"] = [d.model_dump() for d in remaining + requeue]
  save_state(state)

  ui.end_card(tally, before, ownership(state), len(state["pending"]), DECISIONS_FILE)


def ask_choice(prompt, options):
  ui.choice_menu(prompt, options)
  while True:
    choice = read_input() or "1"
    if choice.isdigit() and 1 <= int(choice) <= len(options):
      return options[int(choice) - 1][0]
    ui.note(f"Pick 1–{len(options)}.")


def looks_like_code(path):
  return Path(path).suffix.lower() not in NON_CODE_SUFFIXES and Path(path).name not in NON_CODE_NAMES


if __name__ == "__main__":
  main()
