"""File durability/Windows-lock tests only; never connects to PostgreSQL."""
import errno
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event, Thread
import unittest
from unittest.mock import patch

from strategy_benchmark.artifacts import REPLACE_ATTEMPTS, save_json_new
from strategy_benchmark.engine import Journal


def locked(code=32):
    error = PermissionError("simulated Windows file lock")
    error.winerror = code
    return error


class ArtifactTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "requires real Windows file sharing semantics")
    def test_real_windows_reader_lock_is_retried_until_handle_closes(self):
        with TemporaryDirectory() as directory:
            journal = Journal(directory, {"state": "old"})
            journal.flush()
            journal.data = {"state": "new"}
            reader = journal.path.open("rb")
            collision = Event()
            failures = []
            original = os.replace

            def replace(source, target):
                try:
                    return original(source, target)
                except PermissionError:
                    collision.set()
                    raise

            def writer():
                try:
                    journal.flush()
                except BaseException as exc:
                    failures.append(exc)

            with patch("strategy_benchmark.artifacts.os.replace", side_effect=replace):
                thread = Thread(target=writer)
                thread.start()
                try:
                    self.assertTrue(collision.wait(1), "Windows reader must cause a real sharing violation")
                finally:
                    reader.close()
                    thread.join(3)
            self.assertFalse(thread.is_alive())
            self.assertEqual(failures, [])
            self.assertEqual(json.loads(journal.path.read_text(encoding="utf-8")), {"state": "new"})

    def test_transient_windows_locks_retry_without_destroying_old_journal(self):
        with TemporaryDirectory() as directory:
            journal = Journal(directory, {"status": "pending"})
            journal.flush()
            previous = journal.path.read_bytes()
            journal.data["status"] = "committed"
            original = os.replace
            calls = []

            def replace(source, target):
                calls.append(1)
                if len(calls) <= 2:
                    self.assertEqual(journal.path.read_bytes(), previous)
                    self.assertEqual(json.loads(Path(source).read_text(encoding="utf-8"))["status"], "committed")
                    raise locked(32 if len(calls) == 1 else 5)
                return original(source, target)

            with patch("strategy_benchmark.artifacts.os.replace", side_effect=replace), patch("strategy_benchmark.artifacts.time.sleep") as sleep:
                journal.flush()
            self.assertEqual(len(calls), 3)
            self.assertEqual(sleep.call_count, 2)
            self.assertEqual(json.loads(journal.path.read_text(encoding="utf-8")), {"status": "committed"})
            self.assertFalse(journal.path.with_name("journal.json.tmp").exists())

    def test_persistent_lock_keeps_previous_journal_and_complete_temporary(self):
        with TemporaryDirectory() as directory:
            journal = Journal(directory, {"state": "old"})
            journal.flush()
            previous = journal.path.read_bytes()
            journal.data = {"state": "new"}
            with patch("strategy_benchmark.artifacts.os.replace", side_effect=locked(33)) as replace, patch("strategy_benchmark.artifacts.time.sleep") as sleep:
                with self.assertRaises(PermissionError):
                    journal.flush()
            self.assertEqual(replace.call_count, REPLACE_ATTEMPTS)
            self.assertLessEqual(sum(c.args[0] for c in sleep.call_args_list), 2.25)
            self.assertEqual(journal.path.read_bytes(), previous)
            self.assertEqual(json.loads((Path(directory) / "journal.json.tmp").read_text(encoding="utf-8")), {"state": "new"})

    def test_other_io_errors_fail_immediately_preserving_previous_journal(self):
        with TemporaryDirectory() as directory:
            journal = Journal(directory, {"state": "old"})
            journal.flush()
            previous = journal.path.read_bytes()
            journal.data = {"state": "new"}
            with patch("strategy_benchmark.artifacts.os.replace", side_effect=OSError(errno.ENOSPC, "disk full")) as replace, patch("strategy_benchmark.artifacts.time.sleep") as sleep:
                with self.assertRaises(OSError):
                    journal.flush()
            replace.assert_called_once()
            sleep.assert_not_called()
            self.assertEqual(journal.path.read_bytes(), previous)

    def test_new_result_is_not_visible_until_complete_publication(self):
        with TemporaryDirectory() as directory:
            target = Path(directory) / "cell.json"
            with patch("strategy_benchmark.artifacts.publish_new", side_effect=locked()):
                with self.assertRaises(PermissionError):
                    save_json_new(target, {"status": "ok", "query_plan": [{"Plan": {"Node Type": "Result"}}]})
            self.assertFalse(target.exists())
            temporary = target.with_name(target.name + ".tmp")
            self.assertEqual(json.loads(temporary.read_text(encoding="utf-8"))["status"], "ok")

    def test_new_result_never_overwrites_existing_evidence(self):
        with TemporaryDirectory() as directory:
            target = Path(directory) / "cell.json"
            save_json_new(target, {"message": "完整原始數據"})
            previous = target.read_bytes()
            with self.assertRaises(FileExistsError):
                save_json_new(target, {"message": "replacement"})
            self.assertEqual(target.read_bytes(), previous)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["message"], "完整原始數據")

    def test_publish_race_does_not_replace_another_completed_result(self):
        from strategy_benchmark.artifacts import publish_new

        with TemporaryDirectory() as directory:
            target, temporary = Path(directory) / "cell.json", Path(directory) / "cell.json.tmp"
            target.write_text('{"owner":"existing"}', encoding="utf-8")
            temporary.write_text('{"owner":"new"}', encoding="utf-8")
            with self.assertRaises(FileExistsError):
                publish_new(temporary, target)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["owner"], "existing")


if __name__ == "__main__":
    unittest.main()
