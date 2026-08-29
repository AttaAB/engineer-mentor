def build_pr_context(files): 
  pr_context = ""

  for file in files:
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