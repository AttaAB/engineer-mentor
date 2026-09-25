#!/usr/bin/env python3
"""A tiny fake HTTP file server for trying out sync-cli locally.

Serves every file under --root:
  GET /manifest.json       -> {"files": [{"path", "size", "sha256", "mtime"}, ...]}
  GET /files/<path>        -> raw file bytes

Use --fail-rate to simulate a flaky network: that fraction of requests will
randomly get a 503, a dropped connection, or a truncated body.
"""
import argparse
import hashlib
import json
import os
import random
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def build_manifest(root):
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in sorted(filenames):
            if name.startswith("."):
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            h = hashlib.sha256()
            with open(full, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            st = os.stat(full)
            files.append({"path": rel, "size": st.st_size,
                          "sha256": h.hexdigest(), "mtime": int(st.st_mtime)})
    return {"files": files}


class Handler(BaseHTTPRequestHandler):
    root = "."
    fail_rate = 0.0
    delay = 0.0

    def log_message(self, fmt, *args):
        print("[server] " + fmt % args, flush=True)

    def _maybe_fail(self):
        if random.random() >= self.fail_rate:
            return False
        mode = random.choice(["503", "drop"])
        if mode == "503":
            self.send_error(503, "Simulated outage")
        else:
            self.close_connection = True
            self.connection.close()
        self.log_message("simulated failure (%s) for %s", mode, self.path)
        return True

    def do_GET(self):
        if self.delay:
            time.sleep(self.delay)
        if self._maybe_fail():
            return
        path = urllib.parse.urlparse(self.path).path
        if path == "/manifest.json":
            body = json.dumps(build_manifest(self.root), indent=2).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path.startswith("/files/"):
            rel = urllib.parse.unquote(path[len("/files/"):])
            root = os.path.realpath(self.root)
            full = os.path.realpath(os.path.join(root, rel))
            if not full.startswith(root + os.sep) or not os.path.isfile(full):
                self.send_error(404, "Not found")
                return
            with open(full, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            # Occasionally send a truncated body to exercise integrity checks.
            if self.fail_rate and random.random() < self.fail_rate / 2 and len(data) > 1:
                self.wfile.write(data[: len(data) // 2])
                self.close_connection = True
                self.log_message("simulated truncated body for %s", self.path)
                return
            self.wfile.write(data)
            return
        self.send_error(404, "Not found")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default="remote_files", help="directory to serve")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--fail-rate", type=float, default=0.0,
                   help="fraction of requests to fail (0.0-1.0)")
    p.add_argument("--delay", type=float, default=0.0,
                   help="seconds to wait before answering each request")
    p.add_argument("--seed", action="store_true",
                   help="create a few sample files in --root if it is empty")
    args = p.parse_args()

    os.makedirs(args.root, exist_ok=True)
    if args.seed and not os.listdir(args.root):
        os.makedirs(os.path.join(args.root, "docs"), exist_ok=True)
        samples = {
            "hello.txt": b"hello, world\n",
            "docs/readme.md": b"# Sample\n\nSome remote docs.\n",
            "data.bin": os.urandom(512 * 1024),
        }
        for rel, data in samples.items():
            with open(os.path.join(args.root, rel), "wb") as f:
                f.write(data)
        print(f"[server] seeded {len(samples)} sample files in {args.root}")

    Handler.root = args.root
    Handler.fail_rate = args.fail_rate
    Handler.delay = args.delay
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"[server] serving {os.path.abspath(args.root)} on "
          f"http://{args.host}:{args.port} (fail-rate={args.fail_rate})", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
