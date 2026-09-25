import argparse
import os
import sys

from mentor import git as g
from mentor.context import build_context
from mentor.llm import extract_decisions
from mentor.record import DECISIONS_FILE, load_state, owned_titles, pending_decisions, save_state
from mentor.scope import resolve_scope
from mentor.session import bold, dim, read_input, run_session, QuitSession

QUESTIONS_PER_RUN = 3


def main(argv=None):
  parser = argparse.ArgumentParser(prog="mentor", description="Own the design decisions in code you didn't write.")
  sub = parser.add_subparsers(dest="command", required=True)

  review = sub.add_parser("review", help="review recent changes (or the whole repo)")
  review.add_argument("--all", action="store_true", help="review the whole repo")
  review.add_argument("--uncommitted", action="store_true", help="only uncommitted changes")
  review.add_argument("--since", metavar="REF", help="changes since a commit or date ('3 days ago')")
  review.add_argument("--base", metavar="BRANCH", help="on a branch, compare against BRANCH instead of main")
  review.add_argument("--more", action="store_true", help="continue with decisions left over from the last review")
  review.add_argument("-n", type=int, default=QUESTIONS_PER_RUN, help=f"questions to ask (default {QUESTIONS_PER_RUN})")
  review.add_argument("-v", "--verbose", action="store_true", help="show each pipeline step")

  args = parser.parse_args(argv)

  try:
    os.chdir(g.repo_root())
  except g.GitError:
    sys.exit("mentor: not inside a git repository.")

  try:
    if args.more:
      review_pending(args)
    else:
      review_scope(args)
  except g.GitError as error:
    sys.exit(f"mentor: {error}")


def review_scope(args):
  state = load_state()
  try:
    scope = resolve_scope(args, state, ask_choice)
  except QuitSession:
    return

  if scope.is_empty:
    print(f"Nothing to review ({scope.label}).")
    return

  step(args, "scope", f"{scope.label} · {len(scope.files) + len(scope.untracked)} files · {scope.stats}")

  context, truncated = build_context(scope)
  step(args, "context", f"diff only · {len(context):,} chars")
  if truncated:
    print(dim("  note: change is large; context was truncated. Try a narrower range (--since / --uncommitted)."))

  print(dim("Analyzing design decisions..."))
  decisions = extract_decisions(context, scope.label, owned_titles=owned_titles(state))
  step(args, "decisions", f"{len(decisions)} found · ranked")

  state["last_reviewed_commit"] = g.head_commit()

  if not decisions:
    state["pending"] = []
    save_state(state)
    print("No design decisions worth asking about in this change.")
    return

  asked = decisions[:args.n]
  print()
  print(f"Found {len(decisions)} design decision(s) in {scope.label}.")
  if len(decisions) > len(asked):
    print(f"These {len(asked)} are the ones you'd most likely be asked to explain:")

  finish(state, asked, decisions[args.n:], scope.label)


def review_pending(args):
  state = load_state()
  pending = pending_decisions(state)
  if not pending:
    print("Nothing left over from the last review. Run `mentor review` for new changes.")
    return

  print(f"{len(pending)} decision(s) left from the last review.")
  finish(state, pending[:args.n], pending[args.n:], "continued review")


def finish(state, asked, remaining, scope_label):
  tally, unasked = run_session(asked, state, scope_label)
  state["pending"] = [d.model_dump() for d in unasked + remaining]
  save_state(state)

  left = len(state["pending"])
  print()
  print(dim("═" * 64))
  summary = f"  Owned {tally['owned']} · Partial {tally['partial']} · To revisit {tally['revisit']}"
  if tally["skipped"]:
    summary += f" · Skipped {tally['skipped']}"
  print(bold(summary))
  if left:
    print(dim(f"  {left} more decision(s) — run `mentor review --more`"))
  print(dim(f"  Decision record → {DECISIONS_FILE}"))


def ask_choice(prompt, options):
  print(prompt)
  for number, (_, label) in enumerate(options, start=1):
    print(f"  [{number}] {label}")

  while True:
    choice = read_input("> ") or "1"
    if choice.isdigit() and 1 <= int(choice) <= len(options):
      return options[int(choice) - 1][0]
    print(f"Pick 1–{len(options)}.")


def step(args, name, detail):
  if args.verbose:
    print(dim(f"▸ {name:<10} {detail}"))


if __name__ == "__main__":
  main()
