import base64

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

def get_file_content(contents_url): #fetches a file's full source at the exact commit a changed-file entry points to, decoded from GitHub's base64 encoding
  response = httpx.get(contents_url)
  response.raise_for_status()

  data = response.json()
  return base64.b64decode(data["content"]).decode("utf-8")