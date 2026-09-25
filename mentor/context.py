"""Turn a Scope into the text the model reads.

Session 1 is deliberately diff-only (plus full untracked files). Richer
retrieval — repo map, cross-file references, agent tools — comes in
Sessions 3–4, measured against the eval baseline.
"""

import re
from pathlib import Path

from mentor import git as g
from mentor.scope import exclude_pathspecs

MAX_CONTEXT_CHARS = 150_000
MAX_FILE_CHARS = 40_000

HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def build_context(scope):
  """Return (context_text, truncated)."""
  if scope.kind == "all":
    sections = [_numbered_file(path) for path in scope.files]
  else:
    diff = g.git("diff", scope.base, *exclude_pathspecs())
    sections = [_annotate_diff(diff)] + [_numbered_file(path, new=True) for path in scope.untracked]

  sections = [s for s in sections if s]
  text = ""
  truncated = False
  for section in sections:
    if len(text) + len(section) > MAX_CONTEXT_CHARS:
      truncated = True
      break
    text += section + "\n"

  return text, truncated


def _annotate_diff(diff):
  """Prefix each line of a unified diff with its line number in the new file.

  Lets the model cite `file:line` locations instead of guessing from hunk
  headers. Removed lines get no number because they no longer exist.
  """
  out = []
  new_line = 0

  for line in diff.splitlines():
    if line.startswith("diff --git"):
      out.append("")
      out.append(line)
      continue

    header = HUNK_HEADER.match(line)
    if header:
      new_line = int(header.group(1))
      out.append(line)
    elif line.startswith(("+++", "---", "index ", "new file", "deleted file", "similarity", "rename ", "Binary")):
      out.append(line)
    elif line.startswith("+"):
      out.append(f"{new_line:>5} +{line[1:]}")
      new_line += 1
    elif line.startswith("-"):
      out.append(f"      -{line[1:]}")
    elif line.startswith("\\"):
      continue  # "\ No newline at end of file"
    else:
      out.append(f"{new_line:>5}  {line[1:]}")
      new_line += 1

  return "\n".join(out)


def _numbered_file(path, new=False):
  try:
    content = Path(path).read_text(encoding="utf-8")
  except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
    return ""  # binary, deleted, or not a regular file

  if len(content) > MAX_FILE_CHARS:
    content = content[:MAX_FILE_CHARS] + "\n... (file truncated)"

  marker = "+" if new else " "
  header = f"\nNew untracked file: {path}" if new else f"\nFile: {path}"
  numbered = "\n".join(f"{i:>5} {marker}{line}" for i, line in enumerate(content.splitlines(), start=1))
  return f"{header}\n{numbered}"
