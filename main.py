import httpx

def get_pull_request(owner, repo, pull_number): #function returns the single pull request information
  url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"
  
  response = httpx.get(url)
  response.raise_for_status()
  return response.json()

def get_repo(owner, repo): #function returns the repository information
  url = f"https://api.github.com/repos/{owner}/{repo}"
  
  response = httpx.get(url)
  response.raise_for_status()

  return response.json()

def get_changed_files(owner, repo, pull_number): #function returns the files changed in a pull request and prints the filename, status, changes, and patch for each file
  url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/files"
  
  response = httpx.get(url)
  response.raise_for_status()

  files = response.json()

  for file in files: 
    print("filename:", file["filename"])
    print("status:", file["status"])
    print("additions:", file["additions"])
    print("deletions:", file["deletions"])
    print("patch:", file.get("patch"), end="\n\n")

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


