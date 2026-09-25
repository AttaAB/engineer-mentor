"""Command-line entry point: one-shot or scheduled sync."""
import argparse
import datetime
import fcntl
import os
import signal
import sys
import time

from .remote import Remote, RemoteError, RetryPolicy
from .sync import LOCK_NAME, run_sync


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def stamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_args(argv):
    p = argparse.ArgumentParser(
        prog="sync-cli",
        description="Mirror files from a remote HTTP server into a local folder.")
    p.add_argument("server", help="base URL of the server, e.g. http://127.0.0.1:8000")
    p.add_argument("dest", help="local folder to keep in sync")
    p.add_argument("--manifest-path", default="/manifest.json",
                   help="path of the JSON file listing (default: /manifest.json)")
    p.add_argument("--interval", type=float, default=300,
                   help="seconds between syncs (default: 300)")
    p.add_argument("--once", action="store_true", help="sync once and exit")
    p.add_argument("--dry-run", action="store_true", help="show what would change, do nothing")
    p.add_argument("--retries", type=int, default=5, help="attempts per request (default: 5)")
    p.add_argument("--timeout", type=float, default=30, help="per-request timeout in seconds")
    p.add_argument("--allow-empty", action="store_true",
                   help="allow an empty remote listing to delete all synced files")
    args = p.parse_args(argv)
    if args.interval <= 0 or args.retries < 1:
        p.error("--interval must be > 0 and --retries >= 1")
    return args


def acquire_lock(dest):
    """Prevent two sync-cli processes from writing to the same folder."""
    os.makedirs(dest, exist_ok=True)
    fh = open(os.path.join(dest, LOCK_NAME), "w")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        fh.close()
        return None
    return fh


def sync_once(remote, args):
    log(f"[{stamp()}] syncing {args.server} -> {args.dest}")
    try:
        r = run_sync(remote, args.dest, dry_run=args.dry_run,
                     allow_empty=args.allow_empty, log=log)
    except RemoteError as exc:
        log(f"[{stamp()}] sync failed: {exc}")
        return False
    status = "done" if r.ok else f"done with {len(r.failed)} failure(s)"
    log(f"[{stamp()}] {status}: {r.downloaded} downloaded, {r.deleted} deleted, "
        f"{r.unchanged} unchanged")
    return r.ok


def _raise_interrupt(signum, frame):
    raise KeyboardInterrupt


def main(argv=None):
    args = parse_args(argv)
    lock = acquire_lock(args.dest)
    if lock is None:
        log(f"another sync-cli is already running for {args.dest}")
        return 2

    # Treat SIGTERM like Ctrl+C so partial downloads are cleaned up either way.
    signal.signal(signal.SIGTERM, _raise_interrupt)

    remote = Remote(args.server, args.manifest_path, timeout=args.timeout,
                    retry=RetryPolicy(attempts=args.retries), log=log)
    try:
        if args.once:
            return 0 if sync_once(remote, args) else 1
        log(f"running every {args.interval:g}s; Ctrl+C to stop")
        while True:
            sync_once(remote, args)  # a failed cycle is logged; we retry next cycle
            time.sleep(args.interval)
    except KeyboardInterrupt:
        log("\nstopped")
        return 130
