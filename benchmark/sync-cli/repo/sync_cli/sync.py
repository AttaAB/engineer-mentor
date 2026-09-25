"""Plan and apply a sync from a remote manifest to a local folder.

Only files that sync-cli itself downloaded are ever deleted. Those are tracked
in a state file (.sync-state.json) inside the destination, so unrelated local
files you put in the folder are left alone.
"""
import hashlib
import json
import os
import sys
from dataclasses import dataclass, field

from .progress import FileProgress
from .remote import RemoteError

STATE_NAME = ".sync-state.json"
LOCK_NAME = ".sync.lock"
TMP_SUFFIX = ".sync-part"
RESERVED = {STATE_NAME, STATE_NAME + ".tmp", LOCK_NAME}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class State:
    """Remembers what we downloaded so we can skip unchanged files cheaply
    and know which local files are ours to delete."""

    def __init__(self, dest):
        self.path = os.path.join(dest, STATE_NAME)
        self.files = {}
        try:
            with open(self.path) as f:
                data = json.load(f)
            self.files = dict(data.get("files", {}))
        except FileNotFoundError:
            pass
        except (ValueError, OSError) as exc:
            print(f"warning: ignoring unreadable state file ({exc})", file=sys.stderr)

    def save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"version": 1, "files": self.files}, f, indent=1, sort_keys=True)
        os.replace(tmp, self.path)

    def record(self, rel, local_path, sha):
        st = os.stat(local_path)
        self.files[rel] = {"sha256": sha, "size": st.st_size, "mtime_ns": st.st_mtime_ns}

    def local_sha(self, rel, local_path):
        """sha256 of the local file, using the cached value if the file is untouched."""
        try:
            st = os.stat(local_path)
        except FileNotFoundError:
            return None
        entry = self.files.get(rel)
        if entry and entry.get("size") == st.st_size and entry.get("mtime_ns") == st.st_mtime_ns:
            return entry["sha256"]
        return sha256_file(local_path)


@dataclass
class Plan:
    download: list = field(default_factory=list)
    delete: list = field(default_factory=list)
    unchanged: int = 0


@dataclass
class Result:
    downloaded: int = 0
    deleted: int = 0
    unchanged: int = 0
    failed: list = field(default_factory=list)

    @property
    def ok(self):
        return not self.failed


def local_path_for(dest, rel):
    full = os.path.realpath(os.path.join(dest, *rel.split("/")))
    root = os.path.realpath(dest)
    if not full.startswith(root + os.sep):
        raise ValueError(f"path escapes destination: {rel}")
    return full


def make_plan(remote_files, dest, state):
    plan = Plan()
    remote_paths = set()
    for rf in remote_files:
        if rf.path in RESERVED or rf.path.endswith(TMP_SUFFIX):
            print(f"warning: {rf.path} clashes with a sync-cli file; skipping", file=sys.stderr)
            continue
        remote_paths.add(rf.path)
        lp = local_path_for(dest, rf.path)
        if os.path.isdir(lp):
            print(f"warning: {rf.path} is a local directory; skipping", file=sys.stderr)
            continue
        if state.local_sha(rf.path, lp) == rf.sha256:
            plan.unchanged += 1
            if rf.path not in state.files:
                state.record(rf.path, lp, rf.sha256)  # adopt identical existing file
        else:
            plan.download.append(rf)
    plan.delete = sorted(p for p in state.files if p not in remote_paths)
    return plan


def remove_empty_parents(dest, path):
    root = os.path.realpath(dest)
    d = os.path.dirname(path)
    while d.startswith(root + os.sep):
        try:
            os.rmdir(d)
        except OSError:
            break
        d = os.path.dirname(d)


def run_sync(remote, dest, dry_run=False, allow_empty=False, log=print):
    os.makedirs(dest, exist_ok=True)
    state = State(dest)
    result = Result()

    remote_files = remote.list_files()  # raises RemoteError if unreachable
    plan = make_plan(remote_files, dest, state)
    result.unchanged = plan.unchanged

    # Guard against wiping the mirror because the server briefly returned nothing.
    if not remote_files and plan.delete and not allow_empty:
        log(f"warning: remote manifest is empty; refusing to delete {len(plan.delete)} "
            f"local file(s) (use --allow-empty to permit)")
        plan.delete = []

    log(f"{len(remote_files)} remote file(s): {len(plan.download)} to download, "
        f"{len(plan.delete)} to delete, {plan.unchanged} unchanged")
    if dry_run:
        for rf in plan.download:
            log(f"  would download {rf.path}")
        for p in plan.delete:
            log(f"  would delete {p}")
        return result

    total = len(plan.download)
    for i, rf in enumerate(plan.download, 1):
        lp = local_path_for(dest, rf.path)
        tmp = lp + TMP_SUFFIX
        bar = FileProgress(f"[{i}/{total}] {rf.path}", rf.size)
        try:
            os.makedirs(os.path.dirname(lp), exist_ok=True)
            remote.download(rf, tmp, bar.update)
            os.replace(tmp, lp)  # atomic: never leave a half-written file in place
            state.record(rf.path, lp, rf.sha256)
            state.save()
            result.downloaded += 1
            bar.finish(True)
        except (RemoteError, OSError) as exc:
            bar.finish(False, str(exc))
            result.failed.append(rf.path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    for rel in plan.delete:
        lp = local_path_for(dest, rel)
        try:
            os.remove(lp)
            log(f"  deleted {rel}")
        except FileNotFoundError:
            pass
        except OSError as exc:
            log(f"  could not delete {rel}: {exc}")
            result.failed.append(rel)
            continue
        state.files.pop(rel, None)
        remove_empty_parents(dest, lp)
        result.deleted += 1

    state.save()
    return result
