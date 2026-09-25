import os

from dotenv import load_dotenv
from openai import OpenAI

from mentor.models import DecisionSet, Grade

load_dotenv()

DEFAULT_MODEL = "gpt-5.6-luna"

_client = None


def _get_client():
  global _client
  if _client is None:
    _client = OpenAI()
  return _client


def _model():
  return os.environ.get("MENTOR_MODEL", DEFAULT_MODEL)


EXTRACT_PROMPT = """\
You help developers take ownership of code they did not write themselves —
typically code produced by an AI coding assistant. Such code is full of
design decisions the developer never consciously made: a storage choice, a
concurrency assumption, an error-handling policy, a library, a data shape,
an API contract. The developer will be asked to explain these decisions in
code reviews, incidents, and handoffs.

Your job:
1. Identify the implicit design decisions embedded in the code below.
2. For each, build an answer key FIRST — what was chosen, realistic
   alternatives, concrete consequences, and path:line evidence — then write
   a question that makes the developer derive those consequences.
3. Rank decisions by how much it matters that the developer understands
   them: correctness > reliability > security > architecture > performance
   > maintainability, weighted by real-world impact.

What counts as a decision:
- a choice with realistic alternatives and consequences someone could be
  asked to defend ("why a dict and not Redis?", "why retry 3 times?")
- NOT style, naming, formatting, or trivia
- NOT something the code itself makes obvious and consequence-free

Rules for evidence and grounding:
- Line numbers in the context are the numbers at the start of each line;
  cite them as path:line or path:start-end.
- Every consequence must follow from code you can see. If something is
  missing from the context (e.g. you cannot see whether a DB constraint
  exists), frame it as an assumption to question, and lower confidence.
- Do not invent files, functions, or behaviour.

Rules for questions:
- Pose a concrete scenario and ask the developer to walk through what
  happens ("Two requests arrive at the same moment... what ends up in the
  database?"), rather than asking "why did you choose X?".
- Never state the consequence or the fix inside the question or the setup.
- One decision per question. Answerable in a few sentences.
- The hint nudges toward where to look or what to consider, without
  giving the answer.

{already_owned}
Return between 0 and {max_decisions} decisions. Fewer strong decisions beat
many weak ones; return an empty list if nothing is worth asking about.

Scope: {scope_label}

Code:
{context}
"""

GRADE_PROMPT = """\
You are grading whether a developer understands a design decision in their
own codebase (code they may not have written themselves).

Decision: {title}
Location: {location}
What the code does: {chosen}
Consequences / trade-offs:
{consequences}
Reference answer: {reference_answer}

Question asked: {question}

Developer's answer{attempt_note}:
{answer}

Grade the answer:
- "owned": they identified the core consequence or trade-off, even if
  informally worded or missing secondary details.
- "partial": they are on the right track but missed the central point.
- "missing": wrong, irrelevant, or "I don't know".

Feedback rules:
- Speak directly to the developer ("you"), 1–3 sentences.
- If owned: confirm briefly and add one short insight they didn't mention.
- If partial or missing: say what is right (if anything) and nudge toward
  the gap WITHOUT stating the answer. They may try again.
"""


def extract_decisions(context, scope_label, max_decisions=7, owned_titles=()):
  already_owned = ""
  if owned_titles:
    listed = "\n".join(f"- {t}" for t in owned_titles)
    already_owned = (
      "The developer has already demonstrated ownership of these decisions; "
      "do not return them again unless the code for them has changed:\n"
      f"{listed}\n"
    )

  prompt = EXTRACT_PROMPT.format(
    already_owned=already_owned,
    max_decisions=max_decisions,
    scope_label=scope_label,
    context=context,
  )
  response = _get_client().responses.parse(model=_model(), input=prompt, text_format=DecisionSet)
  return response.output_parsed.decisions


def grade_answer(decision, answer, attempt=1):
  prompt = GRADE_PROMPT.format(
    title=decision.title,
    location=decision.location,
    chosen=decision.chosen,
    consequences="\n".join(f"- {c}" for c in decision.consequences),
    reference_answer=decision.reference_answer,
    question=decision.question,
    attempt_note=f" (attempt {attempt})" if attempt > 1 else "",
    answer=answer,
  )
  response = _get_client().responses.parse(model=_model(), input=prompt, text_format=Grade)
  return response.output_parsed
