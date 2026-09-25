"""The interactive question → answer → grade loop."""

import sys
import textwrap

from mentor.llm import grade_answer
from mentor.record import record_result

MAX_ATTEMPTS = 3

_COLOR = sys.stdout.isatty()


def _style(code, text):
  return f"\033[{code}m{text}\033[0m" if _COLOR else text


def bold(text):
  return _style("1", text)


def dim(text):
  return _style("2", text)


def wrap(text, indent="  "):
  return textwrap.fill(text, width=76, initial_indent=indent, subsequent_indent=indent)


VERDICT_MARKS = {"owned": "✓ Owned.", "partial": "◐ Partial.", "missing": "✗ Not quite."}


class QuitSession(Exception):
  pass


def read_input(prompt="> "):
  try:
    return input(prompt).strip()
  except (EOFError, KeyboardInterrupt):
    print()
    raise QuitSession


def run_session(decisions, state, scope_label):
  """Ask about each decision in turn.

  Returns (tally, requeue): decisions to offer again via --more — the ones
  not reached because the user quit, followed by the ones they skipped.
  """
  tally = {"owned": 0, "partial": 0, "revisit": 0, "skipped": 0}
  skipped = []

  for index, decision in enumerate(decisions):
    try:
      status, answer = ask_decision(decision, index + 1, len(decisions))
    except QuitSession:
      print(dim("\nStopping here — progress saved. Run `mentor review --more` to continue."))
      return tally, decisions[index:] + skipped

    record_result(state, decision, status, answer, scope_label)
    tally[status] += 1
    if status == "skipped":
      skipped.append(decision)

  return tally, skipped


def ask_decision(decision, number, total):
  print()
  print(dim("─" * 64))
  print(bold(f"[{number}/{total}]  {decision.category} · {decision.location}"))
  print()
  print(wrap(decision.setup))
  print()
  print(wrap(f"Q: {decision.question}", indent="  ").replace("  Q:", bold("  Q:"), 1))
  print()
  print(dim("  Type your answer, or [h]int  [e]xplain  [s]kip  [q]uit"))

  attempt = 0
  best = "missing"
  last_answer = None

  while True:
    text = read_input()
    command = text.lower()

    if not text:
      continue
    if command in ("q", "quit"):
      raise QuitSession
    if command in ("s", "skip"):
      return "skipped", last_answer
    if command in ("h", "hint"):
      print(wrap(f"Hint: {decision.hint}"))
      continue
    if command in ("e", "explain"):
      explain(decision)
      return ("partial" if best == "partial" else "revisit"), last_answer

    attempt += 1
    last_answer = text
    print(dim("  grading..."))
    grade = grade_answer(decision, text, attempt)
    print(wrap(f"{VERDICT_MARKS[grade.verdict]} {grade.feedback}"))

    if grade.verdict == "owned":
      return "owned", text
    if grade.verdict == "partial":
      best = "partial"

    if attempt >= MAX_ATTEMPTS:
      explain(decision)
      return ("partial" if best == "partial" else "revisit"), last_answer

    print(dim("  Answer again, or [h]int  [e]xplain  [s]kip  [q]uit"))


def explain(decision):
  print()
  print(bold("  Explanation"))
  print(wrap(decision.reference_answer))
  if decision.alternatives:
    print()
    print("  Alternatives:")
    for alternative in decision.alternatives:
      print(wrap(f"• {alternative}", indent="    "))
