from github_client import get_pull_request, get_changed_files
from mentor import generate_mentor_questions

def main():
  owner = "psf"
  repo = "requests"
  pull_number = 7586

  files = get_changed_files(owner, repo, pull_number)

  print("Changed files:", len(files), end="\n\n")

  for file in files:
      patch = file.get("patch")

      if patch is not None:
        filename = file.get("filename")
        questions = generate_mentor_questions(patch)
        print(f"File: {filename}")
        print(questions, end="\n\n")

if __name__ == "__main__":
    main()


