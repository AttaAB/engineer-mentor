# sync-cli

Keeps a local folder mirrored from a remote HTTP file server. Pure Python 3.9+
standard library, so there's nothing to install (no virtualenv needed). Runs on
macOS/Linux (it uses `fcntl` for the folder lock).

## Try it locally

```sh
# terminal 1: fake server with sample files; --fail-rate 0.3 makes ~30% of requests fail
python3 fake_server.py --root demo/remote --port 8000 --seed --fail-rate 0.3

# terminal 2: sync every 10 seconds (default is every 300s)
./sync-cli http://127.0.0.1:8000 demo/local --interval 10
```

Add, edit, or delete files under `demo/remote/` and watch the next cycle pick
the changes up. Other options: `--once`, `--dry-run`, `--retries N`,
`--timeout S`, `--manifest-path PATH`, `--allow-empty`. `./sync-cli` is a thin
wrapper around `python3 -m sync_cli`.

## What the server must provide

- `GET /manifest.json` returns `{"files": [{"path": "a/b.txt", "size": 123, "sha256": "..."}]}`
  (a bare list works too). An entry can carry its own `"url"`; if it doesn't,
  the file is fetched from `/files/<path>`.

## How it behaves

- **Changes** are detected by sha256. Local hashes are cached in
  `DEST/.sync-state.json` (keyed by size and mtime), so unchanged files aren't
  re-hashed on every cycle. A local file that was edited gets overwritten with
  the remote copy.
- **Downloads** go to a `.sync-part` temp file, get checked against the
  manifest's size and sha256, and are then moved into place atomically. A
  half-finished download never replaces a good file.
- **Deletes** only touch files sync-cli downloaded itself (the ones listed in
  the state file). Files you put in the folder yourself are left alone. If the
  server suddenly returns an empty listing, deletes are skipped unless you pass
  `--allow-empty`.
- **Flaky network:** connection errors, timeouts, truncated bodies, and
  HTTP 408/429/5xx responses are retried with jittered exponential backoff.
  If a file still fails, the rest of the sync carries on and that file is tried
  again next cycle. If the server can't be reached at all, the cycle is logged
  and skipped; scheduled mode keeps running.
- **Safety:** paths from the server that are absolute, contain `..`, or would
  otherwise land outside the destination are rejected. A lock file stops two
  instances from syncing the same folder at once.
- **Exit codes** for `--once`: 0 means success, 1 means some or all of the sync
  failed, 2 means another instance holds the lock. Ctrl+C or SIGTERM returns 130.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

The tests start the fake server in-process, including a run at a 50% failure rate.
