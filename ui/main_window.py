
import os
import json
import datetime
from pathlib import Path

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox, 
    QApplication, QSizePolicy, QDesktopWidget, QFrame, QToolButton, QMenu, QAction
)
from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSignal
from PyQt5.QtGui import QKeyEvent, QIcon, QFont, QPixmap, QPainter, QColor, QBrush, QImage, QPixmapCache

from ui.header_bar import HeaderBar
from ui.side_bar import SideBar
from ui.lesson_intro import LessonIntro
from ui.lesson_runner import LessonRunner
from ui.speed_test_screen import SpeedTestScreen
from ui.speed_test_runner import SpeedTestRunner
from ui.article_selector import ArticleSelector
from ui.practice_screen import PracticeScreen
from ui.practice_runner import PracticeRunner
from ui.admin_panel import AdminPanel
from ui.statistics_tab import StatisticsTab
from ui.user_settings import UserSettingsWindow
from ui.signature_bar import SignatureBar
from ui.user_bar import UserBar
from ui.home_screen import HomeWidget
from utils.tr import tr, set_translation_manager
from utils.translation_manager import TranslationManager
from utils.resource import resource_path
from utils.progress_manager import load_user_progress, save_user_progress
from utils.lessons_loader import load_lessons


class MainWindow(QMainWindow):
    profile_image_updated = pyqtSignal(str)
    
    def __init__(self, app, settings_manager, is_admin=False, user_data=None):
        super().__init__()
        self.app = app
        self.is_admin = is_admin
        self.user_data = user_data
        self.username = user_data.get("username") if user_data else None
        
        # تهيئة المتغيرات الأساسية
        self.settings_manager = settings_manager
        self.translation_manager = TranslationManager(app, settings_manager)
        self.translation_manager.load_translations()
        set_translation_manager(self.translation_manager)
        
        # تهيئة progress قبل استخدامه
        try:
            self.progress = load_user_progress(self.username)
        except Exception as e:
            QMessageBox.critical(self, tr("load_progress_error"), 
                                 tr("load_progress_error_message").format(username=self.username, error=str(e)))
            self.progress = {
                "completed_lessons_ar": [],
                "completed_lessons_en": [],
                "completed_training_levels": [],
                "completed_tests": [],
                "sessions_ar": [],
                "sessions_en": [],
                "practice_sessions": []
            }

        # تحديد مسار مجلد الأنماط
        current_file = Path(__file__).resolve()
        self.styles_dir = current_file.parent.parent / "styles"    
        self.language = settings_manager.get_language()
        
        # تهيئة الواجهة أولاً
        self.setup_ui()
        
        # ثم ترجمة النصوص
        self.retranslate_ui()
    
        # ضمان وجود جميع مفاتيح التقدم
        for key in ["completed_lessons_ar", "completed_lessons_en", "completed_training_levels", "completed_tests"]:
            if key not in self.progress:
                self.progress[key] = []
        
        for key in ["sessions_ar", "sessions_en", "practice_sessions"]:
            if key not in self.progress:
                self.progress[key] = []
                
        self.admin_mode = False
        self.r_press_count = 0
        self.last_key = None
        self.dark_mode = False
        self.lessons_data = load_lessons(self.language)
        self.lesson_keys = self.get_lesson_keys()

        self.setWindowTitle(tr("app_title"))
        self.setWindowIcon(QIcon(resource_path("assets/icons/type.ico")))
        self.setMinimumSize(800, 650)
        self.resize(800, 650)
        self.center_window()

        # إنشاء جميع الواجهات
        self.lesson_intro = LessonIntro(parent=self, on_start=self.start_lesson, lang=self.language)
        self.lesson_runner = LessonRunner()
        self.lesson_runner.lesson_finished.connect(self.end_lesson)
        self.lesson_runner.back_to_main.connect(self.return_to_main_from_lesson)
        self.speed_test_screen = SpeedTestScreen(self.username)
        self.speed_test_runner = SpeedTestRunner()
        self.practice_screen = PracticeScreen(self.username, self.progress)
        self.practice_screen.switch_to_practice_runner.connect(self.show_practice_runner)
        self.practice_runner = PracticeRunner()
        self.practice_runner.set_next_text_available_callback(self.practice_screen.has_next_text)
        self.practice_runner.switch_to_practice_screen.connect(self.back_to_practice_screen)
        self.practice_runner.level_completed_signal.connect(self.handle_level_completed)
        self.practice_runner.next_text_requested.connect(self.show_next_text)
        self.speed_test_runner.test_finished.connect(self.complete_speed_test)
        self.article_selector = ArticleSelector(self.start_speed_test, self.translation_manager)       
        self.sidebar = SideBar(self.select_lesson, self.open_admin_panel, self.translation_manager)
        self.statistics_tab = StatisticsTab(self.progress, self.language, self.lesson_keys)

        # إخفاء كل شيء ما عدا الصفحة الرئيسية
        self.lesson_intro.hide()
        self.lesson_runner.hide()
        self.speed_test_screen.hide()
        self.practice_screen.hide()
        self.speed_test_runner.hide()
        self.article_selector.hide()
        self.sidebar.hide()
        self.practice_runner.hide()
        self.statistics_tab.hide()

        # إضافة جميع الواجهات لمنطقة المحتوى
        self.content_layout.addWidget(self.lesson_intro)
        self.content_layout.addWidget(self.lesson_runner)
        self.content_layout.addWidget(self.speed_test_screen)
        self.content_layout.addWidget(self.speed_test_runner)
        self.content_layout.addWidget(self.article_selector)
        self.content_layout.addWidget(self.practice_screen)
        self.content_layout.addWidget(self.practice_runner)
        self.content_layout.addWidget(self.sidebar)
        self.content_layout.addWidget(self.statistics_tab)

        self.set_light_theme()

        self.speed_test_screen.one_min_btn.clicked.connect(lambda: self.show_article_selector(60))
        self.speed_test_screen.three_min_btn.clicked.connect(lambda: self.show_article_selector(180))
        self.speed_test_screen.five_min_btn.clicked.connect(lambda: self.show_article_selector(300))

        # إنشاء واجهة إعدادات المستخدم
        self.settings_window = UserSettingsWindow(
            parent=self,
            settings=self.settings_manager,
            username=self.username,
            language=self.language
        )
        self.content_layout.addWidget(self.settings_window)
        self.settings_window.hide()

        # إضافة شريط التوقيع في الأسفل
        self.signature_bar = SignatureBar()
        self.main_layout.addWidget(self.signature_bar)

        if not self.is_admin:
            self.admin_panel_widget = None

        self.update_home_tab_states()

    def setup_ui(self):
        # تهيئة العناصر الأساسية
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.central_widget.setLayout(self.main_layout)

        # شريط المستخدم العلوي
        self.user_bar = UserBar(parent=self, username=self.username, user_data=self.user_data, is_admin=self.is_admin)
        self.main_layout.addWidget(self.user_bar)
        # ربط إشارات UserBar بالدوال المناسبة في MainWindow
        self.user_bar.statistics_clicked.connect(self.open_statistics)
        self.user_bar.settings_clicked.connect(self.open_user_settings)
        self.user_bar.language_toggled.connect(self.toggle_language)
        self.user_bar.theme_toggled.connect(self.toggle_theme)
        self.user_bar.logout_clicked.connect(self.logout)
        
        # شريط التبويبات العلوي
        self.header = HeaderBar(self.switch_tab, self.translation_manager, is_admin=self.is_admin, on_admin_panel_open=self.open_admin_panel)
        self.main_layout.addWidget(self.header)
        self.header.hide()

        # منطقة المحتوى الرئيسية
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_area.setLayout(self.content_layout)
        self.main_layout.addWidget(self.content_area, 1)

        # الصفحة الرئيسية
        self.home_widget = HomeWidget(parent=self, is_admin=self.is_admin)
        # ربط إشارة النقر على تبويب في الصفحة الرئيسية
        self.home_widget.on_tab_clicked = self.open_tab_from_home

        # إضافة الصفحة الرئيسية لمنطقة المحتوى
        self.content_layout.addWidget(self.home_widget)

    def retranslate_ui(self):
        """تحديث جميع النصوص عند تغيير اللغة"""
        self.update_texts()
        
    def update_texts(self):
        """تحديث جميع النصوص في الواجهة عند تغيير اللغة"""
        self.setWindowTitle(tr("app_title"))
        # تحديث شريط المستخدم
        if hasattr(self, 'user_bar'):
            self.user_bar.update_texts()
        # تحديث عناصر التبويبات العلوية
        if hasattr(self, 'header') and self.header:
            self.header.update_texts()
        # تحديث أزرار الصفحة الرئيسية
        if hasattr(self, 'home_widget'):
            self.home_widget.update_texts()
        # تحديث عناصر الشريط الجانبي
        if hasattr(self, 'sidebar') and self.sidebar:
            self.sidebar.update_texts()
        # تحديث واجهة الإحصائيات
        if hasattr(self, 'statistics_tab') and self.statistics_tab:
            self.statistics_tab.update_texts()
        # تحديث نافذة الإعدادات
        if hasattr(self, 'settings_window') and self.settings_window:
            self.settings_window.update_texts()
        # تحديث بقية العناصر إذا وجدت
        if hasattr(self, 'lesson_intro') and self.lesson_intro:
            self.lesson_intro.update_texts()
        if hasattr(self, 'lesson_runner') and self.lesson_runner:
            self.lesson_runner.update_texts()
        if hasattr(self, 'speed_test_screen') and self.speed_test_screen:
            self.speed_test_screen.update_texts()
        if hasattr(self, 'speed_test_runner') and self.speed_test_runner:
            self.speed_test_runner.update_texts()
        if hasattr(self, 'article_selector') and self.article_selector:
            self.article_selector.update_texts()
        if hasattr(self, 'practice_screen') and self.practice_screen:
            self.practice_screen.update_texts()
        # تحديث شريط التوقيع
        if hasattr(self, 'signature_bar'):
            self.signature_bar.signature_label.setText("هذا التطبيق وقف لله تعالى - تصميم م. رضا عباس")
        # إعادة رسم الواجهة
        self.repaint()
        QApplication.processEvents()
        self.settings_window = UserSettingsWindow(
            parent=self,
            settings=self.settings_manager,
            username=self.username,
            language=self.language
        )
        self.content_layout.addWidget(self.settings_window)
        self.settings_window.hide()
  
    def center_window(self):
        frame = self.frameGeometry()
        center_point = QDesktopWidget().availableGeometry().center()
        frame.moveCenter(center_point)
        self.move(frame.topLeft())
        # ضبط حجم النافذة ليتناسب مع جميع العناصر
        self.setMinimumHeight(650)
    
    def open_tab_from_home(self, tab_name):
        # إخفاء الصفحة الرئيسية أولاً
        self.home_widget.hide()
        self.header.hide()
        self.setMinimumSize(800, 650)
        self.resize(800, 650)
        self.center_window()
        
        # إظهار شريط المستخدم
        self.user_bar.show()
        
        if tab_name == "lessons":
            self.lesson_intro.show()
            self.sidebar.show()
        elif tab_name == "speed_test":
            self.speed_test_screen.show()
        elif tab_name == "practice_texts":
            self.practice_screen.show()
        elif tab_name == "admin_panel":
            self.open_admin_panel()
            
        self.lesson_runner.hide()
        self.speed_test_runner.hide()
        self.practice_runner.hide()
        self.add_home_button()

    def return_to_home(self):
        # إخفاء جميع الواجهات
        self.hide_all_widgets()
        
        # إظهار العناصر الأساسية للصفحة الرئيسية
        self.user_bar.show()
        self.home_widget.show()
        
        # حذف زر العودة إذا كان موجوداً
        if hasattr(self, 'home_button'):
            self.home_button.deleteLater()
            del self.home_button
    
        # تغيير الحجم
        self.setMinimumSize(800, 650)
        self.resize(800, 650)
        self.center_window()
        self.update_ui()
        QTimer.singleShot(100, self.set_focus_to_active_panel)

    def return_to_main_from_lesson(self):
        self.return_to_home()

    def get_lesson_keys(self):
        keys = []
        for group, lessons in self.lessons_data.items():
            for idx, lesson in enumerate(lessons):
                lesson_name = lesson.get("name")
                if not lesson_name:
                    print(f"[تحذير] الدرس بدون name: {lesson}")
                    continue
                keys.append((group, idx, lesson_name))
        return keys
    
    def update_menu_texts(self):
        # تم نقل هذه الوظيفة إلى UserBar
        pass

    def update_ui(self):
        lang = self.language
        completed_lessons = self.progress.get(f"completed_lessons_{lang}", [])
        self.sidebar.update_lesson_progress(completed_lessons)
        
        # تمكين تبويبات السرعة والنصوص للمدير بغض النظر عن التقدم
        if self.is_admin:
            self.header.set_tab_enabled("practice_texts", True)
            self.header.set_tab_enabled("speed_test", True)
        else:
            all_lessons_completed = self.is_all_lessons_completed()
            self.header.set_tab_enabled("practice_texts", all_lessons_completed)
            completed_trainings = self.progress.get("completed_training_levels", [])
            speed_enabled = len(completed_trainings) > 0
            self.header.set_tab_enabled("speed_test", speed_enabled)
        
        self.sidebar.update_lesson_availability(self.progress, self.lesson_keys)
        self.update_home_tab_states()
        self.repaint()
        QApplication.processEvents()

    def is_all_lessons_completed(self):
        lang = self.language
        completed_lessons = self.progress.get(f"completed_lessons_{lang}", [])
        if not self.lesson_keys:
            return False
        all_lesson_titles = [lesson_id for _, _, lesson_id in self.lesson_keys]
        return all(title in completed_lessons for title in all_lesson_titles)

    def update_home_tab_states(self):
        all_lessons_completed = self.is_all_lessons_completed()
        completed_trainings = self.progress.get("completed_training_levels", [])
        
        # استدعاء الدالة المحدثة في HomeWidget
        if hasattr(self, 'home_widget'):
            self.home_widget.update_tab_states(all_lessons_completed, completed_trainings)

    def toggle_language(self):
        current_lang = self.language
        new_lang = "ar" if current_lang == "en" else "en"
        self.settings_manager.set_language(new_lang)
        self.translation_manager.load_translations()
        self.language = new_lang
        self.lessons_data = load_lessons(self.language)
        self.lesson_keys = self.get_lesson_keys()
        self.progress = load_user_progress(self.username)
        completed_lessons = self.progress.get(f"completed_lessons_{self.language}", [])
        self.sidebar.update_lesson_progress(completed_lessons)
        self.setWindowTitle(tr("app_title"))
        if hasattr(self, "header") and hasattr(self.header, "update_texts"):
            self.header.update_texts()
        if hasattr(self, "sidebar") and hasattr(self.sidebar, "update_texts"):
            self.sidebar.update_texts()
        if hasattr(self, "sidebar") and hasattr(self.sidebar, "reload_lessons"):
            self.sidebar.reload_lessons()
        # تحديث شريط المستخدم العلوي
        if hasattr(self, "user_bar"):
            self.user_bar.update_texts()
        # تحديث الصفحة الرئيسية
        if hasattr(self, "home_widget"):
            self.home_widget.update_texts()
        if hasattr(self.lesson_intro, "update_language"):
            self.lesson_intro.update_language(new_lang)
        if hasattr(self.article_selector, "update_language"):
            self.article_selector.update_language(new_lang)
        if hasattr(self.speed_test_screen, "update_language"):
            self.speed_test_screen.update_language(new_lang)
        if hasattr(self.practice_screen, "update_language"):
            self.practice_screen.update_language(new_lang)
        if hasattr(self.practice_runner, "update_language"):
            self.practice_runner.update_language(new_lang)
        if hasattr(self.speed_test_runner, "update_language"):
            self.speed_test_runner.update_language(new_lang)
        # تحديث واجهات الأدمن بشكل احترافي
        if hasattr(self, "admin_panel_widget") and hasattr(self.admin_panel_widget, "update_language"):
            self.admin_panel_widget.update_language(new_lang)
        self.statistics_tab.update_progress(self.progress, self.language, self.lesson_keys)
        self.update_ui()
        self.update_home_tab_states()
        QApplication.processEvents()
        if hasattr(self.settings_window, 'update_language'):
            self.settings_window.update_language(new_lang)

    def is_lesson_available(self, lesson_title):
        lang = self.language
        completed = self.progress.get(f"completed_lessons_{lang}", [])
        if lesson_title == self.lesson_keys[0][2]:
            return True
        lesson_index = -1
        for i, (group, idx, lesson_id) in enumerate(self.lesson_keys):
            if lesson_id == lesson_title:
                lesson_index = i
                break
        if lesson_index == -1:
            return False
        prev_lesson_id = self.lesson_keys[lesson_index - 1][2]
        return prev_lesson_id in completed

    def toggle_theme(self):
        if self.dark_mode:
            self.set_light_theme()
        else:
            self.set_dark_theme()
        self.dark_mode = not self.dark_mode
        if hasattr(self.settings_window, 'update_theme'):
            self.settings_window.update_theme(self.dark_mode)
        # تحديث شريط التوقيع حسب الوضع الجديد
        if hasattr(self, 'signature_bar'):
            self.signature_bar.update_theme(self.dark_mode)
    
    def load_stylesheet(self, filename):
        try:
            filepath = self.styles_dir / filename
            return filepath.read_text(encoding="utf-8")
        except Exception as e:
            print(f"خطأ في تحميل الأنماط: {e}")
            return ""
    
    def set_light_theme(self):
        style = self.load_stylesheet("app.qss")
        self.setStyleSheet(style)
        # تحديث شريط التوقيع للوضع النهاري
        if hasattr(self, 'signature_bar'):
            self.signature_bar.update_theme(False)
    
    def set_dark_theme(self):
        style = self.load_stylesheet("dark.qss")
        self.setStyleSheet(style)
        # تحديث شريط التوقيع للوضع الليلي
        if hasattr(self, 'signature_bar'):
            self.signature_bar.update_theme(True)
            
    def set_focus_to_active_panel(self):
        try:
            if self.lesson_runner.isVisible():
                self.lesson_runner.set_focus()
            elif self.article_selector.isVisible():
                self.article_selector.set_focus()
            elif self.speed_test_runner.isVisible():
                self.speed_test_runner.set_focus()
            elif self.lesson_intro.isVisible():
                self.lesson_intro.set_focus()
            elif self.practice_screen.isVisible():
                self.practice_screen.set_focus()
            elif self.practice_runner.isVisible():
                self.practice_runner.set_focus()
        except Exception as e:
            print(f"خطأ في تعيين التركيز: {e}")

    def switch_tab(self, name):
        self.hide_all_main_widgets()
        if name == "lessons":
            self.lesson_intro.show()
            self.sidebar.show()
        elif name == "speed_test":
            self.speed_test_screen.show()
        elif name == "practice_texts":
            self.practice_screen.show()
        elif name == "admin_panel":
            if self.is_admin:
                if hasattr(self, 'admin_panel_widget') and self.admin_panel_widget is not None:
                    self.admin_panel_widget.show()
                else:
                    self.open_admin_panel()
            else:
                QMessageBox.warning(self, tr("access_denied"), tr("admin_access_denied"))
        self.header.highlight_tab(name)
        QTimer.singleShot(500, self.set_focus_to_active_panel)
        self.add_home_button()

    def select_lesson(self, lesson_name):
        if not self.is_lesson_available(lesson_name):
            QMessageBox.warning(
                self, 
                tr("lesson_unavailable_title"), 
                tr("lesson_unavailable_message"))
            return
        self.lesson_intro.set_lesson(lesson_name)
        self.lesson_intro.show()
        self.lesson_runner.hide()
        self.speed_test_screen.hide()
        self.speed_test_runner.hide()
        self.article_selector.hide()
        self.sidebar.show()
        QTimer.singleShot(500, self.set_focus_to_active_panel)
        self.add_home_button()

    def start_lesson(self, title, content):
        self.lesson_runner.start_lesson(title, content)
        self.lesson_runner.show()
        self.lesson_intro.hide()
        self.speed_test_screen.hide()
        self.practice_screen.hide()
        self.speed_test_runner.hide()
        self.article_selector.hide()
        self.sidebar.hide()
        QTimer.singleShot(500, self.set_focus_to_active_panel)
        self.add_home_button()

    def show_article_selector(self, duration):
        self.selected_duration = duration
        self.article_selector.set_duration(duration)
        self.article_selector.show()
        self.lesson_intro.hide()
        self.lesson_runner.hide()
        self.practice_screen.hide()
        self.practice_runner.hide()
        self.speed_test_screen.hide()
        self.speed_test_runner.hide()
        self.sidebar.hide()
        QTimer.singleShot(500, self.set_focus_to_active_panel)
        self.add_home_button()

    def start_speed_test(self, text, duration):
        self.article_selector.hide()
        self.speed_test_runner.set_text(text, duration)
        self.speed_test_runner.start_test()
        self.speed_test_runner.show()
        self.sidebar.hide()
        QTimer.singleShot(500, self.set_focus_to_active_panel)
        
    def complete_speed_test(self, wpm, accuracy, duration):
        practice_session = {
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "text": self.speed_test_runner.current_text,
            "duration_seconds": duration,
            "wpm": wpm,
            "accuracy": accuracy
        }
        save_user_progress(self.username, self.progress, practice_session=practice_session)
        
        completed_tests = self.progress["completed_tests"]
        if "speed_test" not in completed_tests:
            completed_tests.append("speed_test")
            save_user_progress(self.username, self.progress)
        
        self.update_ui()    
        
    def open_admin_panel(self):
            if hasattr(self, 'admin_panel_widget') and self.admin_panel_widget is not None:
                self.hide_all_main_widgets()
                self.admin_panel_widget.show()
                return
            self.admin_panel_widget = AdminPanel(self.translation_manager, parent=self)
            self.content_layout.addWidget(self.admin_panel_widget)
            self.hide_all_main_widgets()
            self.admin_panel_widget.show()
            self.add_home_button()

    def close_admin_panel(self):
        if hasattr(self, 'admin_panel_widget') and self.admin_panel_widget is not None:
            self.admin_panel_widget.hide()
        self.lesson_intro.show()
        self.sidebar.show()

    def hide_all_main_widgets(self):
        self.lesson_intro.hide()
        self.lesson_runner.hide()
        self.speed_test_screen.hide()
        self.speed_test_runner.hide()
        self.article_selector.hide()
        self.practice_screen.hide()
        self.practice_runner.hide()
        self.sidebar.hide()
        self.statistics_tab.hide()
        self.settings_window.hide()
        if hasattr(self, 'admin_panel_widget') and self.admin_panel_widget is not None:
            self.admin_panel_widget.hide()
            
    def hide_all_widgets(self):
        """إخفاء جميع الواجهات الرئيسية باستثناء شريط التوقيع"""
        self.home_widget.hide()
        self.lesson_intro.hide()
        self.lesson_runner.hide()
        self.speed_test_screen.hide()
        self.speed_test_runner.hide()
        self.article_selector.hide()
        self.practice_screen.hide()
        self.practice_runner.hide()
        self.sidebar.hide()
        self.statistics_tab.hide()
        self.settings_window.hide()
        self.header.hide()
        self.user_bar.hide()
        
        if hasattr(self, 'admin_panel_widget') and self.admin_panel_widget is not None:
            self.admin_panel_widget.hide()
            
        # إظهار شريط التوقيع فقط
        self.signature_bar.show()
        
    def end_lesson(self):
        lesson_title = self.lesson_runner.current_lesson_title
        lang = self.language
        completed_key = f"completed_lessons_{lang}"
        lesson_index = -1
        if lesson_title and lesson_title not in self.progress[completed_key]:
            self.progress[completed_key].append(lesson_title)
            session = {
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "lesson": lesson_title,
                "duration_seconds": self.lesson_runner.get_duration(),
                "wpm": self.lesson_runner.get_avg_speed(),
                "accuracy": self.lesson_runner.get_accuracy(),
                "errors": self.lesson_runner.get_error_details(),
                "error_count": self.lesson_runner.get_error_count()
            }
            save_user_progress(self.username, self.progress, session=session, lang=self.language)
        else:
            save_user_progress(self.username, self.progress)
        next_lesson_id = None
        for i, (group, idx, lesson_id) in enumerate(self.lesson_keys):
            if lesson_id == lesson_title:
                lesson_index = i
                break
        if lesson_index != -1 and lesson_index + 1 < len(self.lesson_keys):
            next_lesson_id = self.lesson_keys[lesson_index + 1][2]
        self.lesson_runner.hide()
        self.sidebar.show()
        self.lesson_intro.show()
        self.update_ui()
        if next_lesson_id:
            self.lesson_intro.set_lesson(next_lesson_id)
        else:
            self.lesson_intro.show_welcome()
        QTimer.singleShot(500, self.set_focus_to_active_panel)
        
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_R and event.modifiers() & Qt.ShiftModifier:
            if self.last_key == 'R':
                self.r_press_count += 1
            else:
                self.r_press_count = 1
            self.last_key = 'R'
        else:
            self.r_press_count = 0
            self.last_key = None
        if self.r_press_count >= 7:
            self.toggle_admin_mode()
            self.r_press_count = 0
            self.last_key = None
        super().keyPressEvent(event)
        
    def toggle_admin_mode(self):
        self.admin_mode = not self.admin_mode
        if self.admin_mode:
            QMessageBox.information(self, tr("admin_mode_title"), tr("admin_mode_enabled"))
        else:
            QMessageBox.information(self, tr("admin_mode_title"), tr("admin_mode_disabled"))
    
    def add_home_button(self):
        # لا نضيف زر العودة إذا كنا في الواجهة الرئيسية
        if self.home_widget.isVisible():
            return
        
        # إزالة الزر السابق إذا كان موجوداً
        if hasattr(self, 'home_button'):
            self.home_button.deleteLater()
            del self.home_button
            
        # إنشاء زر جديد للعودة إلى الصفحة الرئيسية
        self.home_button = QPushButton(self)
        self.home_button.setIcon(QIcon(resource_path("assets/icons/home.png")))
        self.home_button.setIconSize(QSize(32, 32))
        self.home_button.setFixedSize(40, 40)
        self.home_button.setStyleSheet("""
            QPushButton {
                background: #e3f2fd;
                border-radius: 20px;
                padding: 4px;
            }
            QPushButton:hover {
                background: #bbdefb;
            }
        """)
        self.home_button.setCursor(Qt.PointingHandCursor)
        self.home_button.setToolTip(tr("return_home"))
        self.home_button.clicked.connect(self.return_to_home)
        self.home_button.move(20, 20)
        self.home_button.show()
        self.home_button.raise_()
        
    def show_practice_runner(self, text_data):
        """عرض شاشة التدريب على النص المحدد"""
        self.practice_screen.selected_text = text_data
        self.practice_runner.set_text_data(text_data)
        self.hide_all_main_widgets()
        self.practice_runner.show()
        self.add_home_button()
        QTimer.singleShot(500, self.practice_runner.set_focus)
        
    def back_to_practice_screen(self, session_data=None):
        """العودة إلى شاشة التدريب الرئيسية"""
        self.practice_runner.hide()
        self.practice_screen.show()
        self.add_home_button()
        
        # حفظ بيانات الجلسة إذا كانت متاحة
        if session_data:
            session_data["date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            if "practice_sessions" not in self.progress:
                self.progress["practice_sessions"] = []
            self.progress["practice_sessions"].append(session_data)
            save_user_progress(self.username, self.progress)
        
        self.update_ui()

    def handle_level_completed(self, session):
        """تحديث تقدم المستخدم عند إكمال مستوى"""
        if self.practice_screen.selected_text:
            text_id = self.practice_screen.selected_text.get("id")
            if text_id is not None:
                completed_practice = self.progress.get("completed_practice", {})
                if isinstance(completed_practice, list):
                    completed_practice = {self.language: completed_practice}
                if not isinstance(completed_practice, dict):
                    completed_practice = {}
                lang_completed = completed_practice.setdefault(self.language, [])
                if text_id not in lang_completed:
                    lang_completed.append(text_id)
                self.progress["completed_practice"] = completed_practice
        
        # تحديث شاشة الممارسة بتقدم جديد
        self.practice_screen.update_progress(self.progress)
        
        # العودة إلى شاشة الممارسة مع تمرير بيانات الجلسة
        self.back_to_practice_screen(session)

    def show_next_text(self):
        """عرض النص التالي في نفس المستوى"""
        if self.practice_screen.current_level and self.practice_screen.selected_text:
            level_key = self.practice_screen.current_level.lower()
            texts = self.practice_screen.texts.get(level_key, [])
            
            # ترتيب النصوص حسب الـ ID
            sorted_texts = sorted(texts, key=lambda x: x.get('id', 0))
            
            # البحث عن النص الحالي
            current_id = self.practice_screen.selected_text.get("id")
            next_text_data = None
            
            for i, text_data in enumerate(sorted_texts):
                if text_data.get("id") == current_id and i < len(sorted_texts) - 1:
                    next_text_data = sorted_texts[i + 1]
                    break
            
            # إذا وجد نص تالي، عرضه
            if next_text_data:
                self.show_practice_runner(next_text_data)
            else:
                # إذا لم يكن هناك نص تالي، العودة إلى القائمة
                self.back_to_practice_screen()
                
    def open_user_settings(self):
        # إخفاء جميع الواجهات الحالية أولاً
        self.hide_all_widgets()
        
        # إظهار شريط المستخدم
        self.user_bar.show()
        
        # إظهار واجهة الإعدادات
        self.settings_window.show()
        
        # تغيير حجم النافذة لتناسب واجهة الإعدادات
        self.setMinimumSize(800, 600)
        self.resize(800, 600)
        self.center_window()

    def open_statistics(self):
        # إخفاء جميع الواجهات الحالية أولاً
        self.hide_all_widgets()
        
        # إظهار شريط المستخدم
        self.user_bar.show()
        
        # تحديث وتظهر واجهة الإحصائيات
        self.statistics_tab.update_progress(self.progress, self.language, self.lesson_keys)
        self.statistics_tab.show()
        
        # تغيير حجم النافذة لتناسب واجهة الإحصائيات
        self.setMinimumSize(800, 600)
        self.resize(800, 600)
        self.center_window()
        
        # إضافة زر العودة للصفحة الرئيسية
        self.add_home_button()
        
    def logout(self):
        msg = QMessageBox(self)
        msg.setWindowTitle(tr("logout_title"))
        msg.setText(tr("logout_confirmation"))
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)

        reply = msg.exec_()
        
        if reply == QMessageBox.Yes:
            QApplication.quit()