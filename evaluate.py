from github_client import get_pull_request, get_changed_files
from context import build_pr_context
from mentor import generate_mentor_questions

test_cases = [
    {
        "owner": "psf",
        "repo": "requests",
        "pull_number": 7586,
        "description": "Empty cookie value bug",
        "expected_concept": "falsey value vs missing value",
    },
    {
        "owner": "psf",
        "repo": "requests",
        "pull_number": 7128,
        "description": "Fix for issue #7127",
        "expected_concept": "handling of None values in Python",
    },
    {
        "owner": "psf",
        "repo": "requests",
        "pull_number": 7543,
        "description": "Project metadata URLs",
        "expected_concept": None,
    },
]

def evaluate_pr(owner, repo, pull_number):
    pr = get_pull_request(owner, repo, pull_number)

    files = get_changed_files(owner, repo, pull_number)

    context = build_pr_context(files)

    title = pr.get("title")

    mentor_response = generate_mentor_questions(
        title,
        context
    )

    print("=" * 60)
    print(f"{owner}/{repo} PR #{pull_number}")
    print(f"Title: {title}")

    if len(mentor_response.questions) == 0:
        print("NO_QUESTIONS")
    else:
        for question in mentor_response.questions:
            print(f"\nCategory: {question.category}")
            print(f"Question: {question.question}")

    print()

for case in test_cases:
    evaluate_pr(case["owner"], case["repo"], case["pull_number"])
