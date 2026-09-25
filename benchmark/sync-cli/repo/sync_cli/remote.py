"""HTTP access to the remote server, with retries for a flaky network."""
import http.client
import json
import random
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

# Errors worth retrying: connection problems, timeouts, truncated bodies,
# and server-side (5xx) or rate-limit (429) responses.
RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}


class RemoteError(Exception):
    """A request failed permanently (or ran out of retries)."""


class IntegrityError(Exception):
    """Downloaded bytes did not match the manifest."""


@dataclass(frozen=True)
class RemoteFile:
    path: str
    size: int
    sha256: str
    url: str


def is_safe_relpath(path):
    """Reject paths that could escape the destination folder."""
    if not path or path.startswith("/") or "\\" in path or "\x00" in path:
        return False
    parts = path.split("/")
    return all(p not in ("", ".", "..") for p in parts) and ":" not in parts[0]


class RetryPolicy:
    def __init__(self, attempts=5, base_delay=0.5, max_delay=30.0, sleep=time.sleep):
        self.attempts = attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.sleep = sleep

    def delay(self, attempt):
        # Exponential backoff with full jitter.
        return random.uniform(0, min(self.max_delay, self.base_delay * 2 ** attempt))

    def run(self, fn, describe, log):
        last = None
        for attempt in range(self.attempts):
            try:
                return fn()
            except Exception as exc:  # classified below
                if not is_retryable(exc):
                    raise RemoteError(f"{describe}: {exc}") from exc
                last = exc
                if attempt + 1 < self.attempts:
                    wait = self.delay(attempt)
                    log(f"  retry {attempt + 1}/{self.attempts - 1} for {describe} "
                        f"in {wait:.1f}s ({short_error(exc)})")
                    self.sleep(wait)
        raise RemoteError(f"{describe}: gave up after {self.attempts} attempt(s) "
                          f"({short_error(last)})") from last


def is_retryable(exc):
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in RETRYABLE_STATUS
    return isinstance(exc, (urllib.error.URLError, http.client.HTTPException,
                            ConnectionError, socket.timeout, TimeoutError,
                            IntegrityError, OSError))


def short_error(exc):
    if isinstance(exc, urllib.error.HTTPError):
        return f"HTTP {exc.code}"
    if isinstance(exc, urllib.error.URLError):
        return f"{type(exc.reason).__name__}: {exc.reason}"
    return f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__


class Remote:
    def __init__(self, base_url, manifest_path="/manifest.json", timeout=30.0,
                 retry=None, log=print):
        self.base_url = base_url.rstrip("/")
        self.manifest_url = urllib.parse.urljoin(self.base_url + "/", manifest_path.lstrip("/"))
        self.timeout = timeout
        self.retry = retry or RetryPolicy()
        self.log = log

    def _open(self, url):
        req = urllib.request.Request(url, headers={"User-Agent": "sync-cli"})
        return urllib.request.urlopen(req, timeout=self.timeout)

    def list_files(self):
        """Fetch and validate the remote manifest."""
        def fetch():
            with self._open(self.manifest_url) as resp:
                return resp.read()

        raw = self.retry.run(fetch, "manifest", self.log)
        try:
            data = json.loads(raw)
        except ValueError as exc:
            raise RemoteError(f"manifest is not valid JSON: {exc}") from exc
        entries = data.get("files") if isinstance(data, dict) else data
        if not isinstance(entries, list):
            raise RemoteError("manifest must be a list or an object with a 'files' list")

        files, seen = [], set()
        for e in entries:
            try:
                path, size, sha = e["path"], int(e["size"]), str(e["sha256"]).lower()
            except (KeyError, TypeError, ValueError):
                self.log(f"  skipping malformed manifest entry: {e!r}")
                continue
            if not is_safe_relpath(path):
                self.log(f"  skipping unsafe path from server: {path!r}")
                continue
            if path in seen:
                continue
            seen.add(path)
            url = e.get("url") or f"{self.base_url}/files/{urllib.parse.quote(path)}"
            files.append(RemoteFile(path, size, sha, url))
        return files

    def download(self, rf, dest_tmp, progress):
        """Download rf into dest_tmp, verifying size and sha256. Retries on failure."""
        import hashlib

        def fetch():
            h = hashlib.sha256()
            got = 0
            progress(0)
            with self._open(rf.url) as resp, open(dest_tmp, "wb") as out:
                while True:
                    chunk = resp.read(64 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
                    h.update(chunk)
                    got += len(chunk)
                    progress(got)
            if got != rf.size:
                raise IntegrityError(f"expected {rf.size} bytes, got {got}")
            if h.hexdigest() != rf.sha256:
                raise IntegrityError("sha256 mismatch")

        self.retry.run(fetch, rf.path, self.log)
