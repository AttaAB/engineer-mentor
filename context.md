# Engineering Mentor — Project Context

## 1. Project Overview

**Engineering Mentor** is an AI-powered developer tool designed to help programmers become more thoughtful and effective software engineers.

Unlike traditional AI coding assistants that primarily generate code or directly solve implementation problems, this system is intended to **encourage the developer to reason about their own engineering decisions**.

The mentor analyzes code changes and asks Socratic-style questions about decisions such as:

* Data structure selection
* Algorithmic complexity
* Error handling
* Abstractions
* Function responsibilities
* Maintainability
* Coupling
* API design
* State management
* Security
* Concurrency
* Testing
* Architectural trade-offs

Instead of saying:

> Replace this list with a dictionary.

the mentor should ideally ask something like:

> This function searches through every user when looking up an ID. How does that lookup behave as the number of users grows?

The objective is to make the developer recognize and reason through the trade-off themselves.

---

# 2. Core Product Philosophy

The project is based on one central idea:

> **AI should help developers think better, not simply think for them.**

Most AI coding tools optimize for:

```text
Problem
   ↓
AI generates solution
   ↓
Developer accepts code
```

Engineering Mentor instead aims for:

```text
Developer implementation
        ↓
AI identifies an engineering decision
        ↓
AI asks a thoughtful question
        ↓
Developer reasons about the trade-off
        ↓
AI provides hints if needed
        ↓
Developer arrives at the solution
```

The eventual mentoring progression may look like:

```text
Level 0 — Socratic question
        ↓
Level 1 — Small hint
        ↓
Level 2 — Stronger conceptual hint
        ↓
Level 3 — Explain the relevant concept
        ↓
Level 4 — Pseudocode
        ↓
Level 5 — Implementation, only if necessary
```

The system should avoid giving away the solution prematurely.

---

# 3. Long-Term Vision

The original idea is for the mentor to eventually live inside the developer's IDE and provide context-aware engineering feedback.

Potential future behavior:

```text
Developer writes code
        ↓
Mentor detects a meaningful engineering decision
        ↓
Mentor challenges the developer's reasoning
        ↓
Developer explains or revises the decision
```

Examples:

> Why did you choose a list for this collection?

> What assumptions are you making about this API always succeeding?

> Why should this class be responsible for both persistence and validation?

> How would this design behave with multiple concurrent requests?

However, real-time IDE analysis introduces significant complexity:

* Determining when code is complete enough to analyze
* Avoiding constant interruptions
* Understanding partially written functions
* Maintaining repository context
* Latency
* API cost
* IDE integration
* Developer personalization

Because of this, the project is being built incrementally.

---

# 4. Current Scope — V0/V1

The current version focuses on **GitHub pull requests rather than real-time IDE analysis**.

Current target flow:

```text
GitHub Pull Request
        ↓
Retrieve changed files
        ↓
Retrieve code patches
        ↓
Send patches to an LLM
        ↓
Generate engineering questions
        ↓
Print questions in the terminal
```

This is intentionally much simpler than the eventual product.

The purpose is first to prove:

> Can an LLM examine a real developer's code changes and generate useful engineering questions without simply giving the solution?

---

# 5. Current Architecture

Current architecture:

```text
                  GitHub
                     │
                     ▼
             GitHub REST API
                     │
                     ▼
             github_client.py
                     │
              changed files
                     │
                 patches
                     ▼
                  main.py
                     │
                     ▼
                 mentor.py
                     │
                     ▼
               OpenAI API
                     │
                     ▼
          Engineering Questions
                     │
                     ▼
                 Terminal
```

Current separation of responsibilities:

```text
github_client.py
    ↓
Knows HOW to communicate with GitHub


mentor.py
    ↓
Knows HOW to communicate with the LLM
and generate mentoring questions


main.py
    ↓
Coordinates the overall application
```

This separation is intentional.

`main.py` should describe the application's high-level workflow rather than contain HTTP or LLM implementation details.

---

# 6. Current Technology Stack

The project is intentionally starting with a minimal stack.

## Currently Used

### Python

Primary programming language.

Python was selected because the developer is already syntactically comfortable with it and can therefore focus on:

* APIs
* Software architecture
* AI engineering
* Testing
* Context engineering
* Code analysis

rather than simultaneously learning a new programming language.

---

### HTTPX

Used to communicate with the GitHub REST API.

Example:

```python
response = httpx.get(url)
```

Important concepts learned through HTTPX:

* HTTP requests
* GET requests
* URLs
* HTTP status codes
* JSON responses
* Error handling
* External APIs

---

### GitHub REST API

Currently used to retrieve:

* Pull request metadata
* Changed files
* File patches/diffs

Relevant endpoints:

```text
GET /repos/{owner}/{repo}/pulls/{pull_number}
```

Retrieves metadata for one pull request.

```text
GET /repos/{owner}/{repo}/pulls/{pull_number}/files
```

Retrieves the files changed in that pull request.

---

### OpenAI Python SDK

Used to communicate with an LLM.

Conceptually:

```text
Python application
      ↓
OpenAI SDK
      ↓
OpenAI API
      ↓
LLM
```

Example:

```python
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="...",
    input=prompt
)
```

---

### Git / GitHub

Used for source control and repository hosting.

---

### Python Virtual Environment

The project uses:

```text
.venv/
```

to isolate Python dependencies from other projects.

The environment is created once:

```bash
python3 -m venv .venv
```

and activated for new terminal sessions with:

```bash
source .venv/bin/activate
```

on macOS/Linux.

---

# 7. Technologies Intentionally NOT Added Yet

The project is deliberately avoiding premature complexity.

Not currently being used:

```text
FastAPI
React
Next.js
TypeScript
LangChain
LangGraph
Redis
Celery
PostgreSQL
Docker
Kubernetes
Vector databases
RAG frameworks
Agent frameworks
Tree-sitter
```

Some of these may eventually become appropriate.

The principle is:

> **Introduce technology when the project encounters a concrete problem that requires it.**

For example:

```text
Need automatic GitHub webhook handling
        ↓
Introduce FastAPI
```

rather than:

```text
FastAPI seems popular
        ↓
Add FastAPI immediately
```

---

# 8. Current Project Structure

Current structure is approximately:

```text
engineering-mentor/
│
├── main.py
├── github_client.py
├── mentor.py
├── README.md
├── .gitignore
└── .venv/
```

Possible future structure:

```text
engineering-mentor/
│
├── app/
│   ├── main.py
│   │
│   ├── github/
│   │   ├── client.py
│   │   └── webhooks.py
│   │
│   ├── analysis/
│   │   ├── diff.py
│   │   ├── context.py
│   │   └── code_parser.py
│   │
│   ├── mentor/
│   │   ├── prompts.py
│   │   └── model.py
│   │
│   └── models/
│
├── tests/
├── .env
├── .gitignore
├── README.md
└── pyproject.toml
```

This future architecture should **not be implemented prematurely**.

---

# 9. GitHub Client — Current Functionality

The GitHub-specific functions live in:

```text
github_client.py
```

## `get_pull_request`

Purpose:

> Retrieve metadata for a specific GitHub pull request.

Conceptually:

```python
def get_pull_request(owner, repo, pull_number):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"

    response = httpx.get(url)
    response.raise_for_status()

    return response.json()
```

Example usage:

```python
pr = get_pull_request(
    "psf",
    "requests",
    7586
)

print(pr["title"])
```

Important concept:

A request for **one resource** typically returns a JSON object, which becomes a Python dictionary.

---

## `get_changed_files`

Purpose:

> Retrieve all files changed in a specific pull request.

Conceptually:

```python
def get_changed_files(owner, repo, pull_number):
    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/pulls/{pull_number}/files"
    )

    response = httpx.get(url)
    response.raise_for_status()

    return response.json()
```

The returned value is a list because the endpoint can return multiple files.

Each file may contain information such as:

```text
filename
status
additions
deletions
changes
patch
```

Example:

```python
files = get_changed_files(
    "psf",
    "requests",
    7586
)

for file in files:
    print(file["filename"])
```

---

# 10. Understanding Patches

The `patch` field contains the code difference associated with a changed file.

Example:

```diff
- users = []
+ users = {}
```

General interpretation:

```text
- line
```

means that line was removed.

```text
+ line
```

means that line was added.

The patch is currently the primary input given to the mentor LLM.

Current flow:

```text
Pull Request
      ↓
Changed File
      ↓
Patch
      ↓
Mentor
```

The system currently uses:

```python
patch = file.get("patch")
```

rather than:

```python
patch = file["patch"]
```

because a patch may not always be present.

`.get()` safely returns `None` if the key does not exist.

---

# 11. Current Mentor Implementation

The LLM functionality lives in:

```text
mentor.py
```

Its central function is:

```python
generate_mentor_questions(patch)
```

Current conceptual implementation:

```python
from openai import OpenAI


client = OpenAI()


def generate_mentor_questions(patch):
    prompt = f"""
    You are a software engineering mentor.

    Your goal is to help a developer think critically about their
    implementation rather than giving them the solution.

    Review the following code.

    Ask 3 concise questions about meaningful engineering decisions.

    Focus on things such as:
    - data structure choices
    - complexity
    - maintainability
    - error handling
    - design trade-offs

    Do not provide replacement code.
    Do not directly tell the developer what to change.

    Code:
    {patch}
    """

    response = client.responses.create(
        model="...",
        input=prompt
    )

    return response.output_text
```

The exact model may change and should not be considered part of the architecture.

---

# 12. Current `main.py`

`main.py` currently coordinates GitHub retrieval and mentor generation.

Approximate current implementation:

```python
from github_client import get_changed_files
from mentor import generate_mentor_questions


def main():
    owner = "psf"
    repo = "requests"
    pull_number = 7586

    files = get_changed_files(
        owner,
        repo,
        pull_number
    )

    print(
        "Changed files:",
        len(files),
        end="\n\n"
    )

    for file in files:
        patch = file.get("patch")

        if patch is not None:
            filename = file["filename"]

            questions = generate_mentor_questions(
                patch
            )

            print(f"File: {filename}")
            print(
                questions,
                end="\n\n"
            )


if __name__ == "__main__":
    main()
```

Current end-to-end flow:

```text
main()
  ↓
get_changed_files()
  ↓
GitHub API
  ↓
files
  ↓
for each file
  ↓
patch
  ↓
generate_mentor_questions()
  ↓
OpenAI API
  ↓
questions
  ↓
terminal
```

---

# 13. Current Product State

At this point, **V0 exists end-to-end**.

The application can approximately do:

```text
Real public GitHub PR
          ↓
Retrieve changed files
          ↓
Extract patches
          ↓
Send patches to an LLM
          ↓
Generate engineering questions
          ↓
Display questions
```

This is the first primitive implementation of the central product idea.

---

# 14. Important Current Limitations

The current implementation is intentionally naive.

## Limitation 1 — Patch-only context

The LLM currently sees approximately:

```text
patch
```

and nothing else.

This may cause incorrect or shallow feedback because the patch may reference:

* Functions defined elsewhere
* Classes defined elsewhere
* Imported modules
* Repository architecture
* Calling functions
* External interfaces

Example:

```python
result = cache.get(user_id)
```

The patch alone does not explain what `cache.get()` actually does.

This will eventually motivate a **context retrieval system**.

---

## Limitation 2 — One LLM request per changed file

Current behavior:

```text
file 1 → LLM
file 2 → LLM
file 3 → LLM
file 4 → LLM
```

Possible consequences:

* High API cost
* Slow execution
* Repetitive feedback
* Too many questions
* Missing relationships between files
* No PR-level understanding

This should not be optimized prematurely.

It should first be observed through actual testing.

---

## Limitation 3 — Forced question count

The current prompt asks for approximately three questions.

Potential problem:

A perfectly reasonable code change may not deserve three questions.

A future mentor policy may instead allow:

```text
0–5 worthwhile questions
```

rather than forcing meaningless feedback.

---

## Limitation 4 — Raw text output

Currently:

```python
generate_mentor_questions()
```

returns plain text.

Example:

```text
1. Why did you...
2. What happens...
3. How would...
```

This is difficult for software to manipulate.

Eventually the system may use structured output:

```json
{
  "questions": [
    {
      "category": "complexity",
      "question": "How does this lookup behave as the collection grows?"
    }
  ]
}
```

This will enable:

* Filtering
* Ranking
* Evaluation
* Storing questions
* Attaching questions to code locations
* Comparing models

Pydantic may eventually be introduced for this.

---

# 15. Next Immediate Phase — Manual Evaluation

Before adding significant infrastructure, the current V0 should be tested against real public GitHub pull requests.

Recommended PR characteristics:

```text
small bug fixes
small features
small refactors
error-handling changes
1–3 changed files
```

Avoid initially:

```text
huge refactors
dozens of changed files
generated code
documentation-only PRs
dependency lockfile changes
```

For each PR, evaluate the mentor manually.

Questions to ask:

```text
Did it notice a meaningful engineering decision?

Did it ask about an actual trade-off?

Did it ask something already obvious from the code?

Did it misunderstand the code?

Did it hallucinate a problem?

Did it give away the solution?

Was the question educational?

Were questions repetitive?

Would a developer actually benefit from answering this?
```

Save examples of:

```text
Good questions
Bad questions
Repetitive questions
Overly obvious questions
Questions that reveal the answer
Hallucinated concerns
```

These observations should drive the next prompt changes.

---

# 16. Prompt Engineering Philosophy

Prompt changes should not be made merely because wording sounds better.

Preferred process:

```text
Observed bad behavior
        ↓
Identify why it occurred
        ↓
Modify mentor policy/prompt
        ↓
Run same examples again
        ↓
Compare behavior
```

Example:

If the mentor repeatedly asks trivial style questions:

```text
Observed:
"Could this variable name be clearer?"
```

Possible prompt update:

```text
Do not comment on trivial style or naming unless it creates
a meaningful correctness or maintainability issue.

Prioritize:

1. Correctness
2. Architecture/design
3. Complexity
4. Reliability
5. Maintainability
```

This is the beginning of **AI system behavior engineering**, not simply API usage.

---

# 17. Future Context Engine

A major eventual problem is giving the model enough repository context without providing the entire repository.

Naively doing:

```text
whole repository → LLM
```

is undesirable because of:

* Context limits
* Cost
* Latency
* Irrelevant information
* Information overload

Instead, the project may eventually implement:

```text
Changed code
    ↓
Identify relevant symbols
    ↓
Find related definitions
    ↓
Find related callers/dependencies
    ↓
Retrieve relevant context
    ↓
Mentor LLM
```

Possible context hierarchy:

```text
Repository summary
      ↓
Directory summaries
      ↓
File summaries
      ↓
Function/class summaries
```

Only relevant summaries/code would be included in an LLM request.

---

# 18. Future Code Analysis

Initially, code is treated mostly as text.

Eventually the project may need to understand:

```text
Which function changed?
What class is it inside?
What functions does it call?
What imports does it use?
What variables/types appear?
```

For Python, the first likely tool is:

```python
import ast
```

Conceptually:

```text
Python source code
      ↓
parser
      ↓
Abstract Syntax Tree
      ↓
structured code representation
```

Example:

```python
def find_user(user_id):
    return users[user_id]
```

might conceptually become:

```text
FunctionDefinition
│
├── name: find_user
├── arguments
│    └── user_id
└── Return
     └── Subscript
```

Once multi-language support becomes necessary, Tree-sitter may replace or supplement Python's built-in AST tooling.

---

# 19. Future GitHub Integration

The current application is manually run from the terminal.

Current:

```text
python main.py
```

Future:

```text
Developer opens PR
        ↓
GitHub webhook
        ↓
Backend
        ↓
Analyze PR
        ↓
Generate mentor questions
        ↓
Post GitHub review comments
```

This future version will likely introduce:

```text
GitHub App
FastAPI
Webhooks
Authentication
Permissions
```

These technologies should only be added once the mentor itself produces useful feedback.

---

# 20. Future IDE Version

Once the PR-based version works well, the project may expand into a VS Code extension.

Possible intermediate version:

```text
Developer writes code
        ↓
Clicks "Challenge My Implementation"
        ↓
Current changes are analyzed
        ↓
Mentor asks questions
```

This is preferable before fully automatic real-time intervention.

A later version may trigger on:

```text
file save
commit
test run
completed function
large refactor
```

Potential IDE stack:

```text
VS Code Extension
    ↓
TypeScript
    ↓
Python backend
    ↓
Mentor/context engine
```

---

# 21. Future Developer Knowledge Model

A longer-term idea is for the mentor to adapt to what the developer already understands.

For example:

```text
Developer repeatedly demonstrates strong knowledge of hash maps
        ↓
Mentor stops asking basic hash-map questions
        ↓
Mentor begins asking deeper architecture/concurrency questions
```

Conceptual skill model:

```text
Hash maps          — strong
Recursion          — moderate
REST API design    — moderate
Concurrency        — beginner
Database indexing  — beginner
```

The system could progressively increase question difficulty.

This is a long-term feature and is **not part of the current implementation**.

---

# 22. Future LLM Evaluation

A major project goal is eventually comparing different models for mentor quality.

Instead of evaluating models subjectively, the project may create an evaluation dataset containing intentionally designed engineering decisions.

Examples:

```text
Repeated O(n) lookup
Missing API failure handling
Overloaded function responsibility
Global mutable state
Poor abstraction
Tight coupling
Race condition
Caching issue
Incorrect API boundary
Security weakness
```

Different models could be evaluated on metrics such as:

### Issue Detection

Did the model identify the important engineering decision?

### Relevance

Was the question actually worth asking?

### Pedagogy

Did the question encourage reasoning?

### Answer Leakage

Did the model simply reveal the solution?

### Hallucination

Did the model claim a problem existed when it did not?

### Question Quality

Was the question specific, understandable, and actionable?

### Redundancy

Did it repeat the same observation in multiple forms?

This may eventually become a formal benchmark for the mentor system.

---

# 23. Important Design Principle — Avoid Overengineering

The project is intentionally built incrementally.

Do not jump immediately to:

```text
Agent frameworks
Vector databases
Microservices
Full repository indexing
Real-time IDE integration
Complex authentication
Large databases
Multi-model orchestration
```

Preferred progression:

```text
Make simplest version work
        ↓
Use it
        ↓
Observe limitation
        ↓
Understand limitation
        ↓
Introduce technology that solves it
```

Example:

```text
Patch lacks context
        ↓
Retrieve full file
        ↓
Still lacks context
        ↓
Retrieve related symbols
        ↓
Repository becomes too large
        ↓
Build selective context retrieval
```

This progression is intentional because the project is also being used as a software-engineering learning project.

---

# 24. Developer Learning Context

The developer building this project is comfortable with the basic syntax of:

```text
Python
C
```

but has limited prior experience with:

```text
Python libraries
Web frameworks
Backend frameworks
External APIs
AI SDKs
Large independent software projects
```

The developer is intentionally learning these technologies while building the project.

The goal is **not merely to complete the product**.

The goal is also to understand:

```text
why each component exists
how it works
what trade-offs were made
how the architecture evolved
how to explain the project technically
```

---

# 25. How AI Assistants Should Help With This Project

When assisting with this project, behave as an **engineering mentor/pair programmer**, not simply as a code generator.

The developer wants code when necessary, but explanations should support learning.

Preferred teaching pattern:

```text
1. Explain what we are trying to accomplish.

2. Explain the important underlying concept.

3. Show relevant code or a small example.

4. Explain why the code works.

5. Let the developer implement/adapt a portion when reasonable.

6. Ask a transfer question using a slightly different scenario.
```

Example:

```text
Current project:
Write a function that retrieves GitHub pull-request files.

Transfer question:
If you were building another tool that retrieves pull-request commits,
what endpoint/function structure would likely change?
```

The purpose of the transfer question is to verify understanding rather than memorization.

---

# 26. Assistance Style

When providing help:

### Do

* Explain technical concepts intuitively.
* Show concrete examples.
* Explain important syntax.
* Explain architectural trade-offs.
* Provide working code when needed.
* Break large tasks into understandable steps.
* Ask the developer to reason about transferable concepts.
* Point out why a technology is being introduced.
* Explain errors rather than merely replacing broken code.
* Gradually reduce hand-holding as concepts become familiar.
* Help the developer be able to explain the project in interviews.

### Avoid

* Dumping an entire implementation without explanation.
* Introducing unnecessary frameworks.
* Overengineering the project.
* Treating every coding problem as an excuse to use AI agents.
* Giving answers without explaining the transferable concept.
* Rewriting large sections of working code unnecessarily.
* Assuming familiarity with libraries/frameworks.
* Hiding important behavior behind framework abstractions before the underlying concept is understood.

---

# 27. Current Concepts Already Learned

Do not assume these concepts need to be re-taught from zero unless confusion appears.

The developer has already worked through:

### Virtual Environments

```text
Why `.venv` exists
Creating vs activating a virtual environment
Project-specific dependencies
```

### APIs

Basic mental model:

```text
Program
   ↓
HTTP request
   ↓
API
   ↓
HTTP response
   ↓
JSON
```

### HTTP

Basic concepts:

```text
GET
status codes
URLs
response objects
```

### JSON

Understands converting:

```text
JSON response
    ↓
response.json()
    ↓
Python dict/list
```

### API vs SDK

Understands:

```text
API = interface exposed by a service

SDK = library/toolkit that makes using the API easier
```

### Classes and Objects

Basic mental model:

```text
Class = blueprint/type

Object = specific instance of a class

Method = function associated with an object/class
```

Example:

```python
client = OpenAI()
```

where:

```text
OpenAI = class
OpenAI() = creates an object
client = variable referencing the object
```

### OpenAI SDK

Basic understanding of:

```python
client.responses.create(...)
```

and:

```python
response.output_text
```

### Python Modules

Understands moving responsibilities into files such as:

```text
github_client.py
mentor.py
main.py
```

and importing functions between them.

### `if __name__ == "__main__"`

Understands that test/execution code should not automatically run when the module is imported.

### Git

Basic use of:

```text
git init
git status
git add
git commit
git push
```

Commit messages generally use imperative descriptions such as:

```text
Add mentor question generation
Fix GitHub response handling
Refactor GitHub client
```

---

# 28. Current Terminology

Useful simple definitions:

### Fix

Correct something that is broken.

```text
fix: prevent crash when password is empty
```

### Refactor

Change code structure without intentionally changing behavior.

```text
refactor: move validation into helper function
```

### Handle

Add logic for a particular situation or edge case.

```text
handle API timeout
handle missing file
```

### Support

Add compatibility or a new capability.

```text
support CSV uploads
support Python 3.14
```

---

# 29. Current Immediate Next Steps

The project should continue approximately in this order.

## Step 1 — Test V0 on real PRs

Run the system on multiple small public GitHub PRs.

---

## Step 2 — Collect mentor outputs

Save examples of:

```text
good feedback
bad feedback
hallucinated feedback
trivial feedback
solution-revealing feedback
repetitive feedback
```

---

## Step 3 — Improve mentor policy

Change the prompt based on observed failures.

Do not force exactly three questions if there are not three worthwhile engineering decisions.

---

## Step 4 — Introduce structured outputs

Instead of raw text:

```text
"1. Why... 2. What..."
```

move toward structured mentor questions.

Possible structure:

```json
{
  "questions": [
    {
      "category": "complexity",
      "question": "...",
      "reason": "..."
    }
  ]
}
```

---

## Step 5 — Improve context

Progress approximately:

```text
patch only
   ↓
patch + full changed file
   ↓
patch + relevant functions/classes
   ↓
selective repository context
```

---

## Step 6 — Introduce code parsing

Start with Python `ast`.

Eventually consider Tree-sitter for multiple languages.

---

## Step 7 — Improve PR-level reasoning

Move from:

```text
three questions per file
```

toward:

```text
analyze entire PR
        ↓
identify highest-value engineering decisions
        ↓
ask only the strongest questions
```

---

## Step 8 — Automate GitHub workflow

Introduce:

```text
GitHub App
FastAPI
webhooks
PR review comments
```

---

## Step 9 — Build evaluation harness

Compare models and mentor prompts using intentionally designed examples and measurable criteria.

---

# 30. Core Technical Problem Statement

The main technical/research question of the project is:

> **How can an AI system understand enough about a developer's code change to identify worthwhile engineering decisions and guide the developer toward reasoning about those decisions without simply solving the problem for them?**

This problem contains several subproblems:

```text
Code retrieval
Code understanding
Context selection
LLM behavior
Pedagogical design
Evaluation
Developer experience
```

---

# 31. Short Description

If a concise explanation is needed:

> Engineering Mentor is an AI-powered developer tool that analyzes pull-request code changes and helps developers improve their software-engineering reasoning. Instead of automatically generating fixes, it identifies meaningful design decisions—such as data structures, complexity, abstractions, and error handling—and responds with Socratic questions and progressively stronger hints. The project will eventually explore repository-context retrieval, code parsing, model evaluation, GitHub integration, and potentially real-time IDE mentoring.

---

# 32. One-Sentence Description

> **An AI developer tool that reviews your code to improve how you think about engineering decisions rather than simply writing the code for you.**

---

# 33. Current Project Status Summary

```text
Environment setup                         ✅

Git repository                            ✅

Python virtual environment                ✅

GitHub API integration                    ✅

Retrieve PR metadata                      ✅

Retrieve changed files                    ✅

Retrieve patches                          ✅

OpenAI API integration                    ✅

Basic mentor prompt                       ✅

Generate questions from patch             ✅

Connect real PR → mentor                  ✅ / current V0

Manual evaluation on multiple real PRs    ← CURRENT FOCUS

Structured mentor outputs                 ⬜

Repository context engine                 ⬜

AST-based code analysis                   ⬜

PR-level question ranking                 ⬜

GitHub App / webhooks                     ⬜

Automated PR comments                     ⬜

Formal LLM evaluation                     ⬜

VS Code extension                         ⬜

Developer knowledge model                 ⬜
```

---

# 34. Guiding Principle Going Forward

When deciding what to build next, ask:

> **What limitation of the current working version are we trying to solve?**

If there is no clear answer, the feature probably does not need to be added yet.

The project should evolve from real problems encountered while using it, not from trying to predict every piece of infrastructure that a mature AI developer tool might eventually need.
