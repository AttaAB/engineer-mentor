from github_client import get_pull_request, get_changed_files

def main():
  owner = "psf"
  repo = "requests"
  pull_number = 7586

  pr = get_pull_request(owner, repo, pull_number)
  print("Title:", pr["title"], end="\n\n")
  print("Changed files:", pr["changed_files"], end="\n\n")
  files = get_changed_files(owner, repo, pull_number)
 # print("keys:", files[0].keys())

if __name__ == "__main__":
    main()


