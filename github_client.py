import httpx

def get_pull_request(owner, repo, pull_number): #function returns the single pull request information
  url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"
  
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
    
  return files

def build_pr_context(owner, repo, pull_number): 
  pr_context = ""

  for file in changed_files:
    filename = file.get("filename")
    patch = file.get("patch")

    if patch is not None:
      pr_context += f"File: {filename}\n"
      pr_context += f"Diff:\n{patch}\n\n"
  
  print("Pull Request Context:\n", pr_context)
  return pr_context

if __name__ == "__main__":
  owner = "psf"
  repo = "requests"
  pull_number = 7128 #other tests: 7128, 7543, 7586

  pr_context = build_pr_context(owner, repo, pull_number)