import os
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fake_server  # noqa: E402
from sync_cli.remote import Remote, RemoteError, RetryPolicy, is_safe_relpath  # noqa: E402
from sync_cli.sync import STATE_NAME, run_sync  # noqa: E402


def quiet(*_):
    pass


class ServerCase(unittest.TestCase):
    fail_rate = 0.0

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.remote_dir = os.path.join(self.tmp.name, "remote")
        self.local_dir = os.path.join(self.tmp.name, "local")
        os.makedirs(os.path.join(self.remote_dir, "sub"))
        self.write("a.txt", b"alpha")
        self.write("sub/b.txt", b"beta" * 1000)

        handler = type("H", (fake_server.Handler,), {
            "root": self.remote_dir, "fail_rate": self.fail_rate,
            "log_message": lambda *a: None})
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.remote = Remote(url, timeout=5, log=quiet,
                             retry=RetryPolicy(attempts=30, base_delay=0.01, max_delay=0.05))

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def write(self, rel, data, root=None):
        path = os.path.join(root or self.remote_dir, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)

    def read_local(self, rel):
        with open(os.path.join(self.local_dir, rel), "rb") as f:
            return f.read()

    def sync(self, **kw):
        return run_sync(self.remote, self.local_dir, log=quiet, **kw)


class SyncTests(ServerCase):
    def test_initial_sync_downloads_everything(self):
        r = self.sync()
        self.assertEqual((r.downloaded, r.deleted, r.failed), (2, 0, []))
        self.assertEqual(self.read_local("sub/b.txt"), b"beta" * 1000)

    def test_second_sync_is_noop(self):
        self.sync()
        r = self.sync()
        self.assertEqual((r.downloaded, r.unchanged), (0, 2))

    def test_changed_added_and_removed_files(self):
        self.sync()
        self.write("a.txt", b"alpha v2")
        self.write("c.txt", b"gamma")
        os.remove(os.path.join(self.remote_dir, "sub/b.txt"))
        r = self.sync()
        self.assertEqual((r.downloaded, r.deleted), (2, 1))
        self.assertEqual(self.read_local("a.txt"), b"alpha v2")
        self.assertFalse(os.path.exists(os.path.join(self.local_dir, "sub")))

    def test_local_edit_is_repaired(self):
        self.sync()
        self.write("a.txt", b"tampered", root=self.local_dir)
        r = self.sync()
        self.assertEqual(r.downloaded, 1)
        self.assertEqual(self.read_local("a.txt"), b"alpha")

    def test_unmanaged_local_files_are_kept(self):
        self.write("mine.txt", b"keep me", root=self.local_dir)
        self.sync()
        self.assertEqual(self.read_local("mine.txt"), b"keep me")

    def test_empty_manifest_does_not_wipe_mirror(self):
        self.sync()
        for rel in ("a.txt", "sub/b.txt"):
            os.remove(os.path.join(self.remote_dir, rel))
        self.assertEqual(self.sync().deleted, 0)
        self.assertTrue(os.path.exists(os.path.join(self.local_dir, "a.txt")))
        self.assertEqual(self.sync(allow_empty=True).deleted, 2)

    def test_dry_run_changes_nothing(self):
        self.sync(dry_run=True)
        self.assertFalse(os.path.exists(os.path.join(self.local_dir, "a.txt")))
        self.assertFalse(os.path.exists(os.path.join(self.local_dir, STATE_NAME)))


class FlakyTests(ServerCase):
    fail_rate = 0.5

    def test_sync_succeeds_despite_flaky_server(self):
        for i in range(10):
            self.write(f"f{i}.bin", os.urandom(50_000))
        r = self.sync()
        self.assertEqual(r.failed, [])
        self.assertEqual(r.downloaded, 12)
        for i in range(10):
            with open(os.path.join(self.remote_dir, f"f{i}.bin"), "rb") as f:
                self.assertEqual(self.read_local(f"f{i}.bin"), f.read())
        leftovers = [n for _, _, fs in os.walk(self.local_dir) for n in fs if n.endswith(".sync-part")]
        self.assertEqual(leftovers, [])


class UnitTests(unittest.TestCase):
    def test_safe_paths(self):
        for ok in ("a", "a/b.txt", "x..y"):
            self.assertTrue(is_safe_relpath(ok), ok)
        for bad in ("", "/etc/passwd", "../x", "a/../../x", "a//b", "a\\b", "./a", "C:/x"):
            self.assertFalse(is_safe_relpath(bad), bad)

    def test_unreachable_server_raises(self):
        remote = Remote("http://127.0.0.1:9", timeout=1, log=quiet,
                        retry=RetryPolicy(attempts=2, base_delay=0.01))
        with self.assertRaises(RemoteError):
            remote.list_files()


if __name__ == "__main__":
    unittest.main()
