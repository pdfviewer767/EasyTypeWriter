import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

from ui.lesson_runner import LessonRunner
from ui.main_window import MainWindow


class LessonFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_accurate_prefix_cannot_complete_a_lesson(self):
        runner = LessonRunner()
        runner.lesson_title = "lesson-1"
        runner.lesson_content = "abc"
        runner.input_box.setPlainText("a")
        runner.total_chars = 1
        runner.correct_chars = 1
        completed = []
        runner.lesson_finished.connect(completed.append)

        with patch("ui.lesson_runner.QMessageBox.warning"):
            runner.end_lesson()

        self.assertEqual(completed, [])
        self.assertEqual(runner.lesson_content, "abc")

    def test_main_window_starts_the_lesson_once(self):
        class WidgetStub:
            def show(self):
                pass

            def hide(self):
                pass

        class RunnerStub(WidgetStub):
            def __init__(self):
                self.starts = []

            def start_lesson(self, title, content):
                self.starts.append((title, content))

        window = type("WindowStub", (), {})()
        window.lesson_runner = RunnerStub()
        window.lesson_intro = WidgetStub()
        window.speed_test_screen = WidgetStub()
        window.practice_screen = WidgetStub()
        window.speed_test_runner = WidgetStub()
        window.article_selector = WidgetStub()
        window.sidebar = WidgetStub()
        window.set_focus_to_active_panel = lambda: None
        window.add_home_button = lambda: None

        with patch("ui.main_window.QTimer.singleShot"):
            MainWindow.start_lesson(window, "lesson-1", "abc")

        self.assertEqual(window.lesson_runner.starts, [("lesson-1", "abc")])


if __name__ == "__main__":
    unittest.main()