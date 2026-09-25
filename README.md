# Engineering Mentor

**Own the design decisions in code you didn't write.**

AI coding assistants make dozens of design decisions for you — a storage
choice, a concurrency assumption, an error-handling policy — and you're
still the one who has to explain them in code review, an incident, or an
interview. `mentor` finds those implicit decisions in your changes, asks
you Socratic questions about them, grades your answers, and keeps a
decision record of what you understand.

## Install

```bash
python -m venv .venv
.venv/bin/pip install -e .
echo "OPENAI_API_KEY=sk-..." > .env
```

## Usage

Run inside any git repository:

```bash
mentor review                  # smart default (see below)
mentor review --uncommitted    # only what's not committed yet
mentor review --since <ref>    # from a commit, or a date like "3 days ago"
mentor review --base develop   # on a branch, compare against develop
mentor review --all            # the whole repo
mentor review --more           # continue with leftover decisions
mentor review -v               # show each pipeline step
```

**Smart default:** on a feature branch, reviews changes since the branch
split from `main`. On `main`, reviews everything since your last review
(the first run asks what to look at). Uncommitted changes are always
included.

During a review, type an answer, or `h` (hint), `e` (explain), `s` (skip),
`q` (quit — progress is saved).

## Output

- `.mentor/DECISIONS.md` — each decision, the alternatives and trade-offs,
  your explanation, and whether you own it.
- `.mentor/state.json` — review state (last reviewed commit, statuses,
  leftover decisions).

## How it works

```text
scope → context → decisions (with hidden answer keys) → questions → grading → record
```

Each decision's answer key — what was chosen, alternatives, consequences,
and `file:line` evidence — is built before the question is written, which
keeps questions grounded and makes answers gradable.

Set `MENTOR_MODEL` to override the default model.
