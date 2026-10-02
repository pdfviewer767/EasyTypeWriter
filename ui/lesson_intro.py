# lesson_intro.py
# شاشة مقدمة الدرس في التطبيق
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QHBoxLayout, QMessageBox, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
import os
import json
from utils.tr import tr
from utils.resource import resource_path, user_data_path

class LessonIntro(QWidget):
    def __init__(self, on_start=None, lang="ar", parent=None, dark_mode=False):
        super().__init__(parent)
        self.on_start = on_start
        self.lang = lang
        self.dark_mode = dark_mode
        self.lesson_id = ""
        self.current_lesson_id = None
        self.lesson_content = ""
        self.all_lessons = {}

        self.setup_ui()
        self.load_lessons_file(lang=lang)
        # self.show_welcome()
        self.apply_global_styles()

    def setup_ui(self):
        self.update_colors()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(20)

        # هنا استخدمنا tr لترجمة عنوان التطبيق
        self.header = QLabel(tr("app_title"))
        self.header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.header, alignment=Qt.AlignTop)

        main_layout.addSpacerItem(QSpacerItem(20, 5, QSizePolicy.Minimum, QSizePolicy.Fixed))

        self.description = QTextEdit()
        self.description.setReadOnly(True)
        self.description.setAlignment(Qt.AlignTop | Qt.AlignRight)
        self.start_btn = QPushButton(tr("start_lesson", "ابدأ التمرين"))
        self.start_btn.setMinimumHeight(50)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.hide()
        self.start_btn.clicked.connect(self.start_lesson)

        btn_container = QHBoxLayout()
        btn_container.addStretch()
        btn_container.addWidget(self.start_btn)
        btn_container.addStretch()
        main_layout.addLayout(btn_container)

        main_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        self.update_styles()
        self.update_background()

    def update_colors(self):
        if self.dark_mode:
            self.title_color = "#ffffff"
            self.title_bg = "#263238"
            self.text_color = "#eceff1"
            self.desc_bg = "#37474f"
            self.border_color = "#455a64"
            self.btn_bg = "#29b6f6"
            self.btn_hover = "#0288d1"
            self.btn_pressed = "#0277bd"
            self.bg_color = "#263238"
        else:
            self.title_color = "#0d47a1"
            self.title_bg = "#e3f2fd"
            self.text_color = "#2c3e50"
            self.desc_bg = "#ffffff"
            self.border_color = "#cfd8dc"
            self.btn_bg = "#1e88e5"
            self.btn_hover = "#1976d2"
            self.btn_pressed = "#1565c0"
            self.bg_color = "#f0f4f8"

    def update_styles(self):
        self.header.setStyleSheet(f"""
            font-size: 22px;
            font-weight: bold;
            color: {self.title_color};
            background-color: {self.title_bg};
            padding: 14px 10px;
            border-radius: 12px;
            margin-bottom: 20px;
        """)

        self.description.setStyleSheet(f"""
            font-size: 16px;
            line-height: 1.6;
            padding: 20px;
            background-color: {self.desc_bg};
            color: {self.text_color};
            border: 1px solid {self.border_color};
            border-radius: 10px;
        """)

        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 18px;
                font-weight: bold;
                min-width: 180px;
                padding: 12px 28px;
                background-color: {self.btn_bg};
                color: white;
                border-radius: 10px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {self.btn_hover};
            }}
            QPushButton:pressed {{
                background-color: {self.btn_pressed};
            }}
        """)

    def update_background(self):
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(self.bg_color))
        self.setPalette(palette)

    def apply_global_styles(self):
        try:
            style_path = resource_path("styles/app.qss")
            if os.path.exists(style_path):
                with open(style_path, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
        except Exception as e:
            print(f"⚠️ {tr('style_load_error')}: {e}")

    def load_lessons_file(self, lang="ar"):
        try:
            lessons_file = user_data_path(os.path.join("data", f"lessons_{lang}.json"))
            if os.path.exists(lessons_file):
                with open(lessons_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    self.all_lessons = {tr("uncategorized", "غير مصنفة"): data}
                elif isinstance(data, dict):
                    self.all_lessons = data
                else:
                    self.all_lessons = {}
            else:
                self.all_lessons = {}
        except Exception as e:
            print(f'❌ {tr("load_lessons_error ")}: {e}')
            self.description.setPlainText(f'{tr("load_lessons_error ")}: {str(e)}')
            self.all_lessons = {}

    def set_lesson(self, lesson_id):
        if not self.all_lessons:
            self.load_lessons_file(lang=self.lang)

        lesson = None
        category_name = None
        for category, lessons in self.all_lessons.items():
            for l in lessons:
                if l.get("name") == lesson_id:
                    lesson = l
                    category_name = category
                    break
            if lesson:
                break

        if not lesson:
            self.description.setPlainText(tr("lesson_data_missing" ))
            self.header.setText(tr("lesson_not_found"))
            self.start_btn.hide()
            return

        self.current_lesson_id = lesson_id
        title = lesson.get("display_title", lesson.get("title", lesson_id))
        description = lesson.get("description", tr("no_description"))
        content = lesson.get("content", "")

        self.header.setText(f'{tr("lesson_label")}: {title} ({category_name})')
        self.description.setPlainText(f"{tr('description_label')}:\n{description}\n\n{tr('content_label')}:\n{content[:200]}...")
        self.description.setAlignment(Qt.AlignTop | Qt.AlignRight)
        self.lesson_id = lesson_id
        self.lesson_content = content
        self.start_btn.show()

    def set_dark_mode(self, dark_mode):
        if self.dark_mode != dark_mode:
            self.dark_mode = dark_mode
            self.update_colors()
            self.update_styles()
            self.update_background()

            if self.current_lesson_id:
                self.set_lesson(self.current_lesson_id)
            else:
                self.show_welcome()

    def start_lesson(self):
        main_window = self.window()

        if hasattr(main_window, "is_lesson_unlocked"):
            if not main_window.is_lesson_unlocked(self.lesson_id):
                QMessageBox.warning(self, tr("lesson_locked"), tr("complete_previous"))
                return

        if self.on_start and self.lesson_content:
            self.on_start(self.lesson_id, self.lesson_content)
            self.start_btn.hide()

    def update_language(self, lang):
        self.lang = lang
        self.load_lessons_file(lang=lang)

        if self.current_lesson_id:
            self.set_lesson(self.current_lesson_id)
        # else:
        #     self.show_welcome()

    def set_focus(self):
        self.start_btn.setFocus()
