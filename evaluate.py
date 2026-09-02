from github_client import get_pull_request, get_changed_files
from context import build_pr_context
from mentor import generate_mentor_questions


test_cases = [
    {
        "owner": "psf",
        "repo": "requests",
        "pull_number": 7586,
    },
    {
        "owner": "psf",
        "repo": "requests",
        "pull_number": 7128,
    },
    {
        "owner": "psf",
        "repo": "requests",
        "pull_number": 7543,
    },
]


for case in test_cases:
    owner = case["owner"]
    repo = case["repo"]
    pull_number = case["pull_number"]

    pr = get_pull_request(owner, repo, pull_number)

    files = get_changed_files(owner, repo, pull_number)

    context = build_pr_context(files)

    title = pr.get("title")

    questions = generate_mentor_questions(
        title,
        context
    )

    print("=" * 60)
    print(f"{owner}/{repo} PR #{pull_number}")
    print(f"Title: {title}")
    print()
    print(questions)
    print()