from github_client import get_pull_request, get_changed_files
from mentor import generate_mentor_questions
from context import build_pr_context

def main():
  owner = "psf"
  repo = "requests"
  pull_number = 7586 #other tests: 7128, 7543, 7586

  pr = get_pull_request(owner, repo, pull_number)

  files = get_changed_files(owner, repo, pull_number)
  context = build_pr_context(files)

  print("Changed files:", len(files), end="\n\n")

  pr_title = pr.get("title")

  mentor_questions = generate_mentor_questions(pr_title, context)
  print(f"Pull Request Title: {pr_title}\n")
  print("Mentor Questions:\n", mentor_questions)

if __name__ == "__main__":
    main()


