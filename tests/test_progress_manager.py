import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from utils.progress_manager import load_user_progress, save_user_progress


class ProgressManagerTests(unittest.TestCase):
    def test_completed_practice_is_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            progress_path = Path(directory) / "user_progress.json"
            with patch(
                "utils.progress_manager.get_progress_file",
                return_value=str(progress_path),
            ):
                save_user_progress(
                    "test-user",
                    {"completed_lessons_ar": [], "completed_lessons_en": []},
                    completed_practice={"ar": ["text-1"]},
                )

                loaded = load_user_progress("test-user")

            self.assertEqual(loaded["completed_practice"], {"ar": ["text-1"]})

    def test_legacy_list_progress_can_be_replaced_and_loaded(self):
        with tempfile.TemporaryDirectory() as directory:
            progress_path = Path(directory) / "user_progress.json"
            progress_path.write_text(
                json.dumps([{"lesson_title": "lesson-1"}]), encoding="utf-8"
            )
            with patch(
                "utils.progress_manager.get_progress_file",
                return_value=str(progress_path),
            ):
                progress = load_user_progress("test-user")
                progress["completed_lessons_ar"].append("lesson-1")
                save_user_progress("test-user", progress)
                loaded = load_user_progress("test-user")

            self.assertEqual(loaded["completed_lessons_ar"], ["lesson-1"])

    def test_corrupt_progress_can_be_recovered_on_save(self):
        with tempfile.TemporaryDirectory() as directory:
            progress_path = Path(directory) / "user_progress.json"
            progress_path.write_text("{broken", encoding="utf-8")
            with patch(
                "utils.progress_manager.get_progress_file",
                return_value=str(progress_path),
            ):
                progress = load_user_progress("test-user")
                progress["completed_lessons_ar"].append("lesson-1")
                save_user_progress("test-user", progress)
                loaded = load_user_progress("test-user")

            self.assertEqual(loaded["completed_lessons_ar"], ["lesson-1"])

    def test_completed_practice_uses_language_scoped_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            progress_path = Path(directory) / "user_progress.json"
            with patch(
                "utils.progress_manager.get_progress_file",
                return_value=str(progress_path),
            ):
                save_user_progress("test-user", {}, lang="ar", completed_practice="text-1")
                save_user_progress("test-user", {}, lang="ar", completed_practice="text-1")
                loaded = load_user_progress("test-user")

            self.assertEqual(loaded["completed_practice"], {"ar": ["text-1"]})


if __name__ == "__main__":
    unittest.main()