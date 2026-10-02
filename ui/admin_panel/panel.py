# admin_panel/panel.py
# لوحة تحكم الأدمن في التطبيق
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QStackedWidget, QListWidget, QListWidgetItem
from PyQt5.QtGui import QIcon
import sys
from PyQt5.QtCore import Qt

# استيراد الشاشات الفرعية
from ui.admin_panel.lesson_manager import AdminLessonManager
from ui.admin_panel.users_manager import UsersManager
from ui.admin_panel.stats_screen import StatsScreen
from ui.admin_panel.settings_screen import SettingsScreen
from ui.admin_panel.backup_screen import BackupScreen
from ui.admin_panel.help_screen import HelpScreen
from ui.admin_panel.static_texts_editor import StaticTextsEditor
from utils.resource import resource_path

# استيراد نظام الترجمة الجديد
from utils.tr import tr
from utils.translation_manager import TranslationManager

class AdminPanel(QWidget):
    
    def update_language(self, lang=None):
        """تحديث نصوص واجهة الأدمن عند تغيير اللغة"""
        self.setWindowTitle(tr("admin_panel"))
        self.header.setText(tr("admin_panel"))
        sidebar_items = [
            tr("sidebar_lesson_manager"),
            tr("sidebar_users_manager"),
            tr("sidebar_stats"),
            tr("sidebar_settings"),
            tr("sidebar_backup"),
            tr("sidebar_help"),
            tr("sidebar_static_texts")
        ]
        self.sidebar.clear()
        for item in sidebar_items:
            self.sidebar.addItem(QListWidgetItem(item))
        # تحديث اتجاه اللغة
        lang = self.translation_manager.get_language() if hasattr(self.translation_manager, "get_language") else "ar"
        self.is_rtl = lang == "ar"
        self.setLayoutDirection(Qt.RightToLeft if self.is_rtl else Qt.LeftToRight)
        # تحديث الشاشات الفرعية
        if hasattr(self, "lesson_manager") and hasattr(self.lesson_manager, "update_language"):
            self.lesson_manager.update_language(lang)
        if hasattr(self, "users_manager") and hasattr(self.users_manager, "update_language"):
            self.users_manager.update_language(lang)
        if hasattr(self, "stats_screen") and hasattr(self.stats_screen, "update_language"):
            self.stats_screen.update_language(lang)
        if hasattr(self, "settings_screen") and hasattr(self.settings_screen, "update_language"):
            self.settings_screen.update_language(lang)
        if hasattr(self, "backup_screen") and hasattr(self.backup_screen, "update_language"):
            self.backup_screen.update_language(lang)
        if hasattr(self, "help_screen") and hasattr(self.help_screen, "update_language"):
            self.help_screen.update_language(lang)
        if hasattr(self, "static_texts_editor") and hasattr(self.static_texts_editor, "update_language"):
            self.static_texts_editor.update_language(lang)
    def __init__(self, translation_manager=None, parent=None):
        super().__init__(parent)
        self.translation_manager = translation_manager or TranslationManager()
        
        # استخدام دالة الترجمة مباشرة
        self.setWindowTitle(tr("admin_panel"))
        self.setMinimumSize(900, 600)
        
        # تحميل ملف التنسيق (QSS) باستخدام resource_path
        try:
            qss_path = resource_path("styles/app.qss")
            with open(qss_path, "r", encoding="utf-8") as f:
                style = f.read()
            self.setStyleSheet(style)
        except Exception as e:
            print(tr("failed_to_load_style"), e)

        # تحديد اتجاه الواجهة
        lang = self.translation_manager.get_language()
        self.is_rtl = lang == "ar"
        self.setLayoutDirection(Qt.RightToLeft if self.is_rtl else Qt.LeftToRight)

        # تخطيط رئيسي رأسي
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # رأس علوي
        self.header = QLabel(tr("admin_panel"))
        self.header.setObjectName("admin_panel_header")
        self.header.setAlignment(Qt.AlignCenter)
       
        self.main_layout.addWidget(self.header)

        # تخطيط أفقي للمحتوى
        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # القائمة الجانبية
        self.sidebar = QListWidget()
        self.sidebar.setMinimumWidth(180)
        self.sidebar.setMaximumWidth(320)
        self.sidebar.setSizePolicy(self.sidebar.sizePolicy().Expanding, self.sidebar.sizePolicy().Expanding)
        
        # إضافة عناصر القائمة
        sidebar_items = [
            tr("sidebar_lesson_manager"),
            tr("sidebar_users_manager"),
            tr("sidebar_stats"),
            tr("sidebar_settings"),
            tr("sidebar_backup"),
            tr("sidebar_help"),
            tr("sidebar_static_texts")
        ]
        
        for item in sidebar_items:
            self.sidebar.addItem(QListWidgetItem(item))

        # منطقة الشاشات الفرعية
        self.stack = QStackedWidget()
        self.stack.setSizePolicy(self.stack.sizePolicy().Expanding, self.stack.sizePolicy().Expanding)

        # دالة مساعدة لإنشاء حاوية مع زر المساعدة
        def wrap_with_help(widget, help_callback):
            container = QWidget()
            vlayout = QVBoxLayout(container)
            vlayout.setContentsMargins(0, 0, 0, 0)
            
            hlayout = QHBoxLayout()
            hlayout.addStretch()
            
            help_btn = QPushButton(tr("help_button"))
            help_btn.setToolTip(tr("help_button_tooltip"))
            help_btn.setFixedSize(32, 32)
            
            # تحميل أيقونة المساعدة باستخدام resource_path
            icon_path = resource_path("assets/icons/help.ico")
            help_btn.setIcon(QIcon(icon_path))
            
            help_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            help_btn.clicked.connect(help_callback)
            
            hlayout.addWidget(help_btn)
            vlayout.addLayout(hlayout)
            vlayout.addWidget(widget)
            return container

        # دالة للانتقال إلى شاشة المساعدة
        def show_help():
            self.sidebar.setCurrentRow(5)  # مؤشر شاشة المساعدة
            self.stack.setCurrentIndex(5)   # تطابق فهرس الشاشة

        # إنشاء الشاشات
        self.lesson_manager = AdminLessonManager(self.translation_manager)
        self.users_manager = UsersManager(self.translation_manager)  # تم التصحيح هنا
        self.stats_screen = StatsScreen(self.translation_manager)
        self.settings_screen = SettingsScreen(self.translation_manager)
        self.backup_screen = BackupScreen(self.translation_manager)
        self.help_screen = HelpScreen(self.translation_manager)
        self.static_texts_editor = StaticTextsEditor(self.translation_manager)

        # إضافة الشاشات إلى الستاك (7 شاشات فقط)
        self.stack.addWidget(wrap_with_help(self.lesson_manager, show_help))
        self.stack.addWidget(wrap_with_help(self.users_manager, show_help))
        self.stack.addWidget(wrap_with_help(self.stats_screen, show_help))
        self.stack.addWidget(wrap_with_help(self.settings_screen, show_help))
        self.stack.addWidget(wrap_with_help(self.backup_screen, show_help))
        self.stack.addWidget(wrap_with_help(self.help_screen, show_help))
        self.stack.addWidget(wrap_with_help(self.static_texts_editor, show_help))

        # إضافة العناصر حسب اتجاه اللغة
        if self.is_rtl:
            self.content_layout.addWidget(self.stack, 1)
            self.content_layout.addWidget(self.sidebar)
        else:
            self.content_layout.addWidget(self.sidebar)
            self.content_layout.addWidget(self.stack, 1)
            
        self.main_layout.addLayout(self.content_layout, 1)

        # ربط تغيير العنصر المحدد في القائمة بتغيير الشاشة
        def handle_sidebar_change(index):
            if 0 <= index < self.stack.count():
                self.stack.setCurrentIndex(index)
                
        self.sidebar.currentRowChanged.connect(handle_sidebar_change)
        self.sidebar.setCurrentRow(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.width() < 600:
            self.sidebar.hide()
        else:
            self.sidebar.show()

# --- كود تشغيل مستقل ---
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication, QMainWindow
    from utils.translation_manager import TranslationManager
    
    app = QApplication(sys.argv)
    
    # تهيئة نظام الترجمة للاختبار
    translation_manager = TranslationManager()
    translation_manager.load_translations()
    
    window = QMainWindow()
    window.setWindowTitle(tr("admin_panel"))
    window.setMinimumSize(950, 650)
    
    panel = AdminPanel(translation_manager=translation_manager)
    window.setCentralWidget(panel)
    window.show()
    
    sys.exit(app.exec_())
