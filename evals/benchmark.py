"""Load benchmark projects and materialize them as throwaway git repos."""

import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel

from mentor.models import Category

BENCHMARK_DIR = Path(__file__).resolve().parent.parent / "benchmark"


class Answers(BaseModel):
  good: str
  partial: str
  wrong: str


class Label(BaseModel):
  id: str
  title: str
  location: str
  also_at: list[str] = []
  category: Category
  priority: Literal["must-find", "nice-to-find"]
  key_point: str
  answers: Answers


class Project(BaseModel):
  project: str
  language: str
  verified: bool = False
  decisions: list[Label]

  @property
  def repo_dir(self):
    return BENCHMARK_DIR / self.project / "repo"


def load_projects(names=None):
  projects = []
  for labels_file in sorted(BENCHMARK_DIR.glob("*/labels.yaml")):
    project = Project(**yaml.safe_load(labels_file.read_text()))
    if names and project.project not in names:
      continue
    projects.append(project)

  missing = set(names or ()) - {p.project for p in projects}
  if missing:
    raise SystemExit(f"Unknown benchmark project(s): {', '.join(sorted(missing))}")
  return projects


@contextmanager
def project_repo(project):
  """Copy a project into a temp dir with one commit, and yield its path."""
  with tempfile.TemporaryDirectory(prefix=f"mentor-eval-{project.project}-") as tmp:
    repo = Path(tmp) / project.project
    shutil.copytree(project.repo_dir, repo)
    for args in (
      ["init", "-q", "-b", "main"],
      ["add", "-A"],
      ["-c", "user.name=eval", "-c", "user.email=eval@local", "commit", "-q", "-m", "snapshot"],
    ):
      subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)
    yield repo
