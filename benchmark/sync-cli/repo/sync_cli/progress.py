"""Minimal progress display: a live bar on a terminal, plain lines otherwise."""
import sys
import time


def fmt_bytes(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024


class FileProgress:
    def __init__(self, label, total, stream=sys.stderr, width=24):
        self.label = label
        self.total = max(total, 0)
        self.stream = stream
        self.width = width
        self.tty = stream.isatty()
        self.start = time.monotonic()
        self._last_draw = 0.0

    def update(self, done):
        if not self.tty:
            return
        now = time.monotonic()
        if done < self.total and now - self._last_draw < 0.1:
            return
        self._last_draw = now
        frac = done / self.total if self.total else 1.0
        filled = int(self.width * min(frac, 1.0))
        rate = done / max(now - self.start, 1e-6)
        self.stream.write(f"\r  {self.label} [{'#' * filled}{'.' * (self.width - filled)}] "
                          f"{frac * 100:5.1f}% {fmt_bytes(done)}/{fmt_bytes(self.total)} "
                          f"{fmt_bytes(rate)}/s\x1b[K")
        self.stream.flush()

    def finish(self, ok, note=""):
        if self.tty:
            self.stream.write("\r\x1b[K")
        mark = "ok" if ok else "FAILED"
        elapsed = time.monotonic() - self.start
        self.stream.write(f"  {self.label} {fmt_bytes(self.total)} {mark} "
                          f"({elapsed:.1f}s){' ' + note if note else ''}\n")
        self.stream.flush()
