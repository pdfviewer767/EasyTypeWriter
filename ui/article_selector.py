# article_selector.py
# شاشة اختيار المقالات في التطبيق
import os
import sys
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QTextEdit, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from utils.resource import resource_path
from utils.tr import tr  # دالة الترجمة

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class ArticleSelector(QWidget):
    def __init__(self, on_article_selected, translation_manager):
        super().__init__()
        self.on_article_selected = on_article_selected
        self.translation_manager = translation_manager
        self.selected_duration = 60
        self.current_level = "Beginner"  # افتراضي

        self.lang = self.translation_manager.get_language()
        self.is_rtl = self.lang == "ar"
        self.setLayoutDirection(Qt.RightToLeft if self.is_rtl else Qt.LeftToRight)

        layout = QVBoxLayout()
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        title = QLabel(tr("article_selector_title", "اختيار المقال"))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.articles = self.load_articles()

        self.article_list = QListWidget()
        self.article_list.setSizePolicy(self.article_list.sizePolicy().Expanding, self.article_list.sizePolicy().Expanding)
        self.flat_articles = []
        self.populate_articles()
        layout.addWidget(self.article_list)

        self.article_preview = QTextEdit()
        self.article_preview.setReadOnly(True)
        self.article_preview.setSizePolicy(self.article_preview.sizePolicy().Expanding, self.article_preview.sizePolicy().Expanding)
        layout.addWidget(self.article_preview)

        self.select_btn = QPushButton(tr("article_selector_start_btn", "ابدأ التمرين"))
        layout.addWidget(self.select_btn)

        self.setLayout(layout)

        try:
            style_path = resource_path("styles/app.qss")
            with open(style_path, "r", encoding="utf-8") as f:
                style = f.read()
            self.setStyleSheet(style)
        except Exception as e:
            print("تعذر تحميل ملف التنسيقات الموحد:", e)

        self.article_list.currentRowChanged.connect(self.update_preview)
        self.select_btn.clicked.connect(self.select_article)

    def set_duration(self, duration):
        """يحافظ على التوافق مع الكود القديم + يحدد المستوى المناسب"""
        self.selected_duration = duration
        if duration == 60:
            self.current_level = "Beginner"
        elif duration == 180:
            self.current_level = "Intermediate"
        elif duration == 300:
            self.current_level = "Advanced"
        else:
            self.current_level = "Beginner"

        # إعادة تحميل المقالات حسب المستوى
        self.populate_articles()

    def load_articles(self):
        lang = self.translation_manager.get_language()
        filename = "tests_ar.json" if lang == "ar" else "tests_en.json"
        path = resource_path(os.path.join("data", filename))
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return {}

    def populate_articles(self):
        """إعادة تعبئة قائمة المقالات حسب المستوى الحالي"""
        self.article_list.clear()
        self.flat_articles = []

        group_articles = self.articles.get(self.current_level, [])
        for article in group_articles:
            art_title = article.get("title", tr("article_no_title", "بدون عنوان"))
            item_text = f"{art_title} - ({self.current_level})"
            item = QListWidgetItem(item_text)
            font = QFont()
            font.setPointSize(15)
            item.setFont(font)
            item.setTextAlignment(Qt.AlignCenter)
            self.article_list.addItem(item)
            self.flat_articles.append(article)

    def update_preview(self, index):
        if 0 <= index < len(self.flat_articles):
            self.article_preview.setPlainText(self.flat_articles[index].get("content", ""))
        else:
            self.article_preview.clear()

    def select_article(self):
        index = self.article_list.currentRow()
        if 0 <= index < len(self.flat_articles):
            selected = self.flat_articles[index]
            self.on_article_selected(selected.get("content", ""), self.selected_duration)

    def set_focus(self):
        if self.article_list.count() > 0:
            self.article_list.setFocus()
            self.article_list.setCurrentRow(0)

    def update_language(self, lang):
        self.lang = lang
        self.is_rtl = self.lang == "ar"
        self.setLayoutDirection(Qt.RightToLeft if self.is_rtl else Qt.LeftToRight)

        self.setWindowTitle(tr("article_selector_title", "اختيار المقال"))
        self.select_btn.setText(tr("article_selector_start_btn", "ابدأ التمرين"))

        # إعادة تحميل المقالات حسب اللغة + المستوى
        self.articles = self.load_articles()
        self.populate_articles()
