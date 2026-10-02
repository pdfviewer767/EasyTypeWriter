import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.practice_runner import PracticeRunner
from ui.practice_screen import PracticeScreen


class PracticeFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_extra_words_reduce_accuracy_and_do_not_pass(self):
        runner = PracticeRunner()
        runner.original_text.setPlainText("one two")
        runner.input_text.setPlainText("one two extra")

        session = runner.get_session_data()

        self.assertAlmostEqual(session["accuracy"], 200 / 3)
        self.assertFalse(session["passed"])
        self.assertEqual(session["total_words"], 3)

    def test_next_text_uses_current_selection_after_progress_refresh(self):
        screen = PracticeScreen("test-user", {})
        screen.texts = {
            "beginner": [
                {"id": 1, "title": "First"},
                {"id": 2, "title": "Second"},
            ]
        }
        screen.show_level_titles("beginner")
        screen.update_progress({"completed_practice": {"ar": [1]}})

        runner = PracticeRunner()
        runner.set_next_text_available_callback(screen.has_next_text)
        self.assertEqual(screen.selected_text["id"], 1)
        self.assertTrue(runner.has_next_text())

        screen.selected_text = screen.texts["beginner"][1]
        self.assertFalse(runner.has_next_text())

    def test_level_completion_uses_one_session_persistence_route(self):
        progress = {"practice_sessions": [], "completed_practice": {}}
        saved_sessions = []

        class PracticeScreenStub:
            selected_text = {"id": 1}

            def update_progress(self, updated_progress):
                pass

        window = SimpleNamespace(
            language="ar",
            progress=progress,
            practice_screen=PracticeScreenStub(),
            back_to_practice_screen=saved_sessions.append,
        )
        session = {"accuracy": 100}

        MainWindow.handle_level_completed(window, session)

        self.assertEqual(progress["completed_practice"], {"ar": [1]})
        self.assertEqual(saved_sessions, [session])


if __name__ == "__main__":
    unittest.main()