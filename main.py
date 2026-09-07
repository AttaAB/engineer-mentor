from github_client import get_pull_request, get_changed_files
from mentor import generate_mentor_questions
from context import build_pr_context


def main():
    owner = "psf"
    repo = "requests"
    pull_number = 7586

    pr = get_pull_request(owner, repo, pull_number)

    files = get_changed_files(owner, repo, pull_number)
    context = build_pr_context(files)

    pr_title = pr.get("title")

    mentor_response = generate_mentor_questions(
        pr_title,
        context
    )

    print("Changed files:", len(files), end="\n\n")
    print(f"Pull Request Title: {pr_title}\n")
    print("Mentor Questions:")

    if len(mentor_response.questions) == 0:
        print("NO_QUESTIONS")
    else:
        for question in mentor_response.questions:
            print(f"\nCategory: {question.category}")
            print(f"Question: {question.question}")


if __name__ == "__main__":
    main()