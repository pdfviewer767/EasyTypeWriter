# settings_screen.py
# شاشة إعدادات التطبيق في لوحة التحكم
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QCheckBox, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
from utils.tr import tr
from utils.translation_manager import TranslationManager  # استيراد الفئة وليس الكائن
from utils.resource import resource_path

class SettingsScreen(QWidget):
    def __init__(self, translation_manager=None, parent=None):
        super().__init__(parent)
        if translation_manager is not None:
            self.translator = translation_manager
        else:
            from utils.tr import set_translation_manager
            from PyQt5.QtWidgets import QApplication
            from core.settings_manager import SettingsManager
            app = QApplication.instance()
            settings_manager = SettingsManager()
            self.translator = TranslationManager(app, settings_manager)
            set_translation_manager(self.translator)
        self.lang = self.translator.get_language() if hasattr(self.translator, "get_language") else "ar"
        self.is_rtl = self.lang == "ar"
        self.setLayoutDirection(Qt.RightToLeft if self.is_rtl else Qt.LeftToRight)

        self.setWindowTitle(self.translator.translate("settings_title"))
        self.setMinimumSize(400, 300)
        self.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Expanding)

        # تحميل ملف التنسيقات باستخدام resource_path
        try:
            qss_path = resource_path("styles/app.qss")
            with open(qss_path, "r", encoding="utf-8") as f:
                style = f.read()
            self.setStyleSheet(style)
        except Exception as e:
            print("تعذر تحميل ملف التنسيقات الموحد:", e)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        # لغة التطبيق
        lang_label = QLabel(self.translator.translate("settings_app_language_label"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems([
            self.translator.translate("settings_lang_ar"), 
            self.translator.translate("settings_lang_en")
        ])
        layout.addWidget(lang_label)
        layout.addWidget(self.lang_combo)

        # المظهر
        theme_label = QLabel(self.translator.translate("settings_theme_label"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            self.translator.translate("settings_theme_light"),
            self.translator.translate("settings_theme_dark"),
            self.translator.translate("settings_theme_auto")
        ])
        layout.addWidget(theme_label)
        layout.addWidget(self.theme_combo)

        # أصوات الكتابة
        self.sounds_checkbox = QCheckBox(self.translator.translate("settings_keyboard_sounds_enable"))
        layout.addWidget(self.sounds_checkbox)

        # زر حفظ الإعدادات
        save_btn = QPushButton(self.translator.translate("settings_save_btn"))
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

    def save_settings(self):
        # مثال لحفظ الإعدادات (يمكنك تطويره لاحقًا)
        QMessageBox.information(
            self, 
            self.translator.translate("settings_save_success_title"), 
            self.translator.translate("settings_save_success_msg")
        )
