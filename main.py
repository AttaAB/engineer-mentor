from github_client import get_pull_request, get_changed_files
from mentor import generate_mentor_questions, generate_mentor_questions1

def main():
  owner = "psf"
  repo = "requests"
  pull_number = 7543 #other tests: 7128, 7543, 7586

  files = get_changed_files(owner, repo, pull_number)

  print("Changed files:", len(files), end="\n\n")

  for file in files:
      filename = file.get("filename")
      patch = file.get("patch")

      if patch is not None:
        filename = file.get("filename")
        questions = generate_mentor_questions1(filename, patch)
        print(f"File: {filename}")
        print(questions, end="\n\n")

if __name__ == "__main__":
    main()


