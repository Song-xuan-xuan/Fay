import os
import sys
import tempfile
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class RuntimeCleanupTest(unittest.TestCase):
    def test_archives_matching_files_and_keeps_unmatched_files(self):
        from utils.runtime_cleanup import archive_runtime_files

        with tempfile.TemporaryDirectory() as temp_dir:
            base = os.path.join(temp_dir, "logs")
            os.makedirs(base)
            self._write(os.path.join(base, "log-old.log"), "old log")
            self._write(os.path.join(base, "keep.txt"), "keep")

            archived = archive_runtime_files(base, lambda name: name.endswith(".log"), batch_id="run-1")

            archived_path = os.path.join(base, "archive", "run-1", "log-old.log")
            self.assertEqual(1, archived)
            self.assertFalse(os.path.exists(os.path.join(base, "log-old.log")))
            self.assertTrue(os.path.exists(archived_path))
            self.assertTrue(os.path.exists(os.path.join(base, "keep.txt")))

    def test_prunes_old_archive_batches(self):
        from utils.runtime_cleanup import archive_runtime_files

        with tempfile.TemporaryDirectory() as temp_dir:
            base = os.path.join(temp_dir, "samples")
            archive_root = os.path.join(base, "archive")
            os.makedirs(archive_root)
            for name in ("old-1", "old-2", "old-3"):
                os.makedirs(os.path.join(archive_root, name))
            self._write(os.path.join(base, "sample-new.wav"), "audio")

            archive_runtime_files(base, lambda name: name.startswith("sample-"), batch_id="run-4", max_archives=2)

            self.assertFalse(os.path.exists(os.path.join(archive_root, "old-1")))
            self.assertFalse(os.path.exists(os.path.join(archive_root, "old-2")))
            self.assertTrue(os.path.exists(os.path.join(archive_root, "old-3")))
            self.assertTrue(os.path.exists(os.path.join(archive_root, "run-4", "sample-new.wav")))

    def _write(self, path, content):
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
