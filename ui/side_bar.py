# side_bar.py   
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QFrame, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
import json
from utils.tr import tr
from utils.resource import resource_path, user_data_path

class SideBar(QWidget):
    def update_lesson_availability(self, progress, lesson_keys):
        """تحديث مفاتيح الدروس فقط (لم يعد هناك حاجة لتقدم كامل هنا)"""
        self.lesson_keys = lesson_keys
        self.load_lessons()

    def update_lesson_progress(self, completed_lessons):
        """تحديث قائمة الدروس المكتملة فقط وإعادة تحميل الدروس"""
        self.completed_lessons = completed_lessons if completed_lessons is not None else []
        self.load_lessons()

    def __init__(self, on_lesson_selected, on_admin_panel_open, translator, dark_mode=False):
        super().__init__()
        self.on_lesson_selected = on_lesson_selected
        self.on_admin_panel_open = on_admin_panel_open
        self.translator = translator
        self.dark_mode = dark_mode
        self.completed_lessons = []  # قائمة الدروس المكتملة
        self.lesson_keys = []  # مفاتيح الدروس

        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.main_layout)

        self.update_background()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_layout.setSpacing(15)
        self.scroll_layout.setContentsMargins(5, 5, 5, 5)
        self.scroll_widget.setStyleSheet("background: transparent;")
        self.scroll_widget.setLayout(self.scroll_layout)

        self.scroll_area.setWidget(self.scroll_widget)
        self.main_layout.addWidget(self.scroll_area)

        self.load_lessons()

    def update_theme(self, dark_mode):
        if self.dark_mode != dark_mode:
            self.dark_mode = dark_mode
            self.update_background()
            self.load_lessons()

    def update_background(self):
        # Update background colors and palette
        palette = self.palette()
        if self.dark_mode:
            palette.setColor(QPalette.Window, QColor("#2c3e50"))
        else:
            palette.setColor(QPalette.Window, QColor("#f0f2f5"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    def set_dark_mode(self, dark_mode):
        if self.dark_mode != dark_mode:
            self.dark_mode = dark_mode
            self.update_background()
            self.load_lessons()

    def set_lesson_keys(self, lesson_keys):
        self.lesson_keys = lesson_keys
        self.load_lessons()

    def is_lesson_completed(self, lesson_id):
        return lesson_id in self.completed_lessons

    def is_lesson_available(self, lesson_id):
        if not self.lesson_keys:
            return False
        if lesson_id == self.lesson_keys[0][2]:
            return True
        lesson_index = -1
        for i, (group, idx, l_id) in enumerate(self.lesson_keys):
            if l_id == lesson_id:
                lesson_index = i
                break
        if lesson_index == -1:
            return False
        prev_lesson_id = self.lesson_keys[lesson_index - 1][2]
        return self.is_lesson_completed(prev_lesson_id)

    def load_lessons(self):
        self.clear_layout(self.scroll_layout)
        self.lesson_buttons = {}

        title_color = "#ecf0f1" if self.dark_mode else "#005f99"
        group_color = "#bdc3c7" if self.dark_mode else "#444"
        button_bg = "#34495e" if self.dark_mode else "#ffffff"
        button_text = "#ecf0f1" if self.dark_mode else "#333333"
        button_border = "#2c3e50" if self.dark_mode else "#e0e0e0"
        completed_color = "#2ecc71" if self.dark_mode else "#27ae60"
        disabled_color = "#7f8c8d" if self.dark_mode else "#95a5a6"

        lang = self.translator.get_language()
        if lang == "ar":
            file_path = user_data_path("data/lessons_ar.json")
        else:
            file_path = user_data_path("data/lessons_en.json")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                lessons_data = json.load(file)
        except Exception as e:
            lessons_data = {}
            print(f"⚠️ فشل في تحميل الدروس: {e}")

        title = QLabel(tr("lesson_list"))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            font-size: 20px; 
            font-weight: bold; 
            color: {title_color};
            padding: 10px 0;
            border-bottom: 2px solid {button_border};
        """)
        self.scroll_layout.addWidget(title)

        for group, lessons in lessons_data.items():
            group_label = QLabel(f"{self.translator.translate('group_prefix')} {group}")
            group_label.setStyleSheet(f"""
                font-weight: bold; 
                font-size: 16px; 
                color: {group_color};
                padding: 8px 5px;
                margin-top: 15px;
            """)
            self.scroll_layout.addWidget(group_label)

            for idx, lesson in enumerate(lessons):
                lesson_title = lesson.get("title", "No Title")
                lesson_id = lesson.get("name")
                if not lesson_id:
                    print(f"[تحذير] الدرس بدون name: {lesson_title}")
                    continue

                display_title = lesson_title
                if self.is_lesson_completed(lesson_id):
                    display_title = f"✓ {lesson_title}"

                btn = QPushButton(display_title)

                if idx == 0:
                    btn.setStyleSheet(f"""
                        font-size: 16px; 
                        padding: 10px 15px;
                        text-align: left;
                        border: 1px solid {button_border};
                        border-radius: 5px;
                        background-color: {button_bg};
                        color: {button_text};
                    """)
                    btn.setCursor(Qt.PointingHandCursor)
                    def safe_select_first(checked=False, id=lesson_id):
                        self.on_lesson_selected(id)
                    btn.clicked.connect(safe_select_first)
                elif self.is_lesson_completed(lesson_id):
                    btn.setStyleSheet(f"""
                        font-size: 16px; 
                        padding: 10px 15px;
                        text-align: left;
                        border: 1px solid {completed_color};
                        border-radius: 5px;
                        background-color: {button_bg};
                        color: {completed_color};
                        font-weight: bold;
                    """)
                    btn.setCursor(Qt.PointingHandCursor)
                    btn.clicked.connect(lambda checked, id=lesson_id: self.on_lesson_selected(id))
                elif self.is_lesson_available(lesson_id):
                    btn.setStyleSheet(f"""
                        font-size: 16px; 
                        padding: 10px 15px;
                        text-align: left;
                        border: 1px solid {button_border};
                        border-radius: 5px;
                        background-color: {button_bg};
                        color: {button_text};
                    """)
                    btn.setCursor(Qt.PointingHandCursor)
                    btn.clicked.connect(lambda checked, id=lesson_id: self.on_lesson_selected(id))
                else:
                    btn.setStyleSheet(f"""
                        font-size: 16px; 
                        padding: 10px 15px;
                        text-align: left;
                        border: 1px solid {disabled_color};
                        border-radius: 5px;
                        background-color: {button_bg};
                        color: {disabled_color};
                    """)
                    def show_locked_msg(checked=False, title=lesson_title):
                        QMessageBox.warning(self, "تنبيه", f"لم تنتهي بعد من الدرس السابق للوصول إلى: {title}")
                    btn.clicked.connect(show_locked_msg)
                    btn.setToolTip("أكمل الدرس السابق أولاً")
                self.scroll_layout.addWidget(btn)
                self.lesson_buttons[lesson_id] = btn

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(f"background-color: {button_border};")
        self.scroll_layout.addWidget(separator)

    def update_texts(self):
        for lesson_id in self.lesson_keys:
            btn = self.lesson_buttons.get(lesson_id)
            if btn:
                btn.setText(tr(lesson_id))

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def reload_lessons(self):
        self.load_lessons()
        self.update_texts()
