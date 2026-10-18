import importlib.util
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

spec = importlib.util.spec_from_file_location("upload", Path(__file__).with_name("upload.py"))
upload = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload)


class UploadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.binary = Path(self.temp.name) / "test.bin"
        self.payload = bytes(range(256)) * 8
        self.binary.write_bytes(self.payload)
        self.digest = hashlib.sha256(self.payload).hexdigest()
        self.missing = {"size": None, "sha256": None, "free": 1000000}
        self.match = {"size": len(self.payload), "sha256": self.digest, "free": 1000000}

    def tearDown(self):
        self.temp.cleanup()

    def test_preflight_full_flash_makes_no_changes(self):
        board = Mock()
        board.inspect.return_value = dict(self.missing, free=100)
        with self.assertRaisesRegex(RuntimeError, "Insufficient board flash"):
            upload.upload(board, self.binary)
        board.command.assert_not_called()

    def test_existing_identical_file_is_verified_without_recopy(self):
        board = Mock()
        board.inspect.return_value = self.match
        name, digest, size = upload.upload(board, self.binary)
        self.assertEqual(name, upload.PREFIX + "_" + self.digest[:12])
        self.assertEqual((digest, size), (self.digest, len(self.payload)))
        board.command.assert_not_called()

    def test_mismatched_existing_file_never_overwritten(self):
        board = Mock()
        board.inspect.return_value = dict(self.match, sha256="wrong")
        with self.assertRaisesRegex(RuntimeError, "refusing overwrite"):
            upload.upload(board, self.binary)
        board.command.assert_not_called()

    def test_upload_checks_staged_and_final_hashes(self):
        board = Mock()
        board.inspect.side_effect = [self.missing, self.missing, self.match, self.match]
        name, _, _ = upload.upload(board, self.binary)
        self.assertEqual(board.inspect.call_count, 4)
        calls = board.command.call_args_list
        self.assertEqual(calls[1].args[:2], ("fs", "cp"))
        self.assertIn("os.rename", calls[2].args[1])
        self.assertIn(name + ".bin", calls[2].args[1])
        self.assertNotIn("remove", "".join(str(c) for c in calls))

    def test_incomplete_transfer_never_selected_and_cleans_only_own_stage(self):
        board = Mock()
        board.inspect.side_effect = [self.missing, self.missing,
                                     dict(self.match, size=len(self.payload)//2)]
        with self.assertRaisesRegex(RuntimeError, "size or SHA-256 mismatch"):
            upload.upload(board, self.binary)
        calls = board.command.call_args_list
        self.assertNotIn("os.rename", str(calls))
        self.assertIn("os.remove('/bitstreams/.rtu_vga_", calls[-1].args[1])
        self.assertNotIn("main.py", str(calls))
        self.assertNotIn("config.ini", str(calls))

    def test_start_runs_generated_helper_in_ram_without_upload(self):
        board = Mock()
        project = upload.PREFIX + "_" + self.digest[:12]
        def command(action, filename):
            self.assertEqual(action, "run")
            source = Path(filename).read_text()
            self.assertIn('PROJECT = "' + project + '"', source)
            return "started\n"
        board.command.side_effect = command
        upload.start(board, project)
        filename = board.command.call_args.args[1]
        self.assertFalse(Path(filename).exists())


if __name__ == "__main__":
    unittest.main()
