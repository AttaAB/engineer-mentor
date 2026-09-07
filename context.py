import ast
import re

from github_client import get_file_content

CALL_PATTERN = re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')


def build_pr_context(files):
  pr_context = ""

  for file in files:
    filename = file.get("filename")
    patch = file.get("patch")

    if patch is None:
      continue

    pr_context += f"File: {filename}\n"
    pr_context += f"Diff:\n{patch}\n\n"

    local_defs = _get_referenced_local_definitions(file)
    if local_defs:
      pr_context += f"Referenced local definitions in {filename} (for context, not part of the diff):\n"
      for name, source in local_defs.items():
        pr_context += f"\n{source}\n"
      pr_context += "\n"

  print("Pull Request Context:\n", pr_context)
  return pr_context


def _get_referenced_local_definitions(file):
  filename = file.get("filename")
  patch = file.get("patch")
  contents_url = file.get("contents_url")

  if not filename or not filename.endswith(".py") or not contents_url:
    return {}

  called_names = _extract_called_names(patch)
  if not called_names:
    return {}

  try:
    file_content = get_file_content(contents_url)
  except Exception:
    return {}

  return _extract_local_definitions(file_content, called_names)


def _extract_called_names(patch):
  called = set()

  for line in patch.splitlines():
    if line.startswith("+") and not line.startswith("+++"):
      code_line = line[1:].strip()

      # Skip definition lines themselves — "def foo(" is not a call to foo,
      # it's the definition being added, which is already in the diff.
      if code_line.startswith("def ") or code_line.startswith("async def "):
        continue

      called.update(CALL_PATTERN.findall(code_line))

  return called


def _extract_local_definitions(file_content, names):
  try:
    tree = ast.parse(file_content)
  except SyntaxError:
    return {}

  lines = file_content.splitlines()
  definitions = {}

  for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names:
      start = node.lineno - 1
      end = node.end_lineno
      definitions[node.name] = "\n".join(lines[start:end])

  return definitions


if __name__ == "__main__":
  from github_client import get_changed_files

  owner = "psf"
  repo = "requests"
  pull_number = 7586 #other tests: 7128, 7543, 7586

  files = get_changed_files(owner, repo, pull_number)
  pr_context = build_pr_context(files)
