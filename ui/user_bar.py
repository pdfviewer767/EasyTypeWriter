from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QMenu, QAction, QSizePolicy, QToolButton
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from .user_avatar import AvatarButton
from utils.resource import resource_path
from utils.tr import tr

class UserBar(QFrame):
    # إضافة إشارات للأحداث
    statistics_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    language_toggled = pyqtSignal()
    theme_toggled = pyqtSignal()
    logout_clicked = pyqtSignal()
    
    def __init__(self, parent=None, username=None, user_data=None, is_admin=False):
        super().__init__(parent)
        self.username = username
        self.user_data = user_data
        self.is_admin = is_admin
        
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet("background-color: #e3f2fd; border-bottom: 1px solid #bbdefb;")
        self.setFixedHeight(50)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        user_bar_layout = QHBoxLayout(self)
        user_bar_layout.setContentsMargins(10, 0, 20, 0)
        user_bar_layout.setSpacing(15)
        user_bar_layout.addStretch()

        # اسم المستخدم
        self.username_label = QLabel(self.username)
        self.username_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1976d2;")
    
        # زر الصورة للمستخدم
        self.avatar_button = AvatarButton()
        self.avatar_button.set_user_data(self.username, self.user_data)
        
        # إنشاء القائمة المنسدلة
        self.setup_user_menu()
        
        # تجميع الصورة والاسم
        avatar_name_layout = QHBoxLayout()
        avatar_name_layout.setContentsMargins(0, 0, 0, 0)
        avatar_name_layout.setSpacing(10)
        
        avatar_name_layout.addWidget(self.avatar_button)
        avatar_name_layout.addWidget(self.username_label)

        # إضافة إلى الشريط
        user_bar_layout.addLayout(avatar_name_layout)
        
    def setup_user_menu(self):
        """إعداد القائمة المنسدلة للمستخدم"""
        user_menu = QMenu()
        user_menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #90caf9;
                border-radius: 10px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 30px 8px 20px;
                font-size: 14px;
            }
            QMenu::item:selected {
                background-color: #e3f2fd;
                border-radius: 5px;
            }
        """)
        
        # إضافة خيار الإحصائيات
        statistics_action = QAction(tr("statistics"), self)
        statistics_action.triggered.connect(self.on_statistics_clicked)
        user_menu.addAction(statistics_action)
        
        # إضافة خيار الإعدادات
        settings_action = QAction(QIcon(resource_path("assets/icons/setting.ico")), tr("user_settings"), self)
        settings_action.triggered.connect(self.on_settings_clicked)
        user_menu.addAction(settings_action)
        
        # إضافة خيار تبديل اللغة
        self.language_action = QAction(tr("language"), self)
        self.language_action.triggered.connect(self.on_language_toggle)
        user_menu.addAction(self.language_action)
        
        # إضافة خيار تبديل الوضع الليلي
        self.theme_action = QAction(tr("theme"), self)
        self.theme_action.triggered.connect(self.on_theme_toggle)
        user_menu.addAction(self.theme_action)
        
        # إضافة خيار تسجيل الخروج
        logout_action = QAction(tr("logout"), self)
        logout_action.triggered.connect(self.on_logout_clicked)
        user_menu.addAction(logout_action)
        
        self.avatar_button.setMenu(user_menu)
        self.avatar_button.setPopupMode(QToolButton.InstantPopup)
        
    def update_texts(self):
        """تحديث النصوص عند تغيير اللغة"""
        self.language_action.setText(tr("language"))
        self.theme_action.setText(tr("theme"))
        
        # تحديث عناصر القائمة المنسدلة
        menu = self.avatar_button.menu()
        if menu:
            actions = menu.actions()
            if len(actions) > 0:
                actions[0].setText(tr("statistics"))
            if len(actions) > 1:
                actions[1].setText(tr("user_settings"))
            if len(actions) > 2:
                actions[2].setText(tr("language"))
            if len(actions) > 3:
                actions[3].setText(tr("theme"))
            if len(actions) > 4:
                actions[4].setText(tr("logout"))
    
    def set_user_data(self, username, user_data):
        """تحديث بيانات المستخدم"""
        self.username = username
        self.user_data = user_data
        self.username_label.setText(username)
        self.avatar_button.set_user_data(username, user_data)
        
    # معالجات الأحداث
    def on_statistics_clicked(self):
        self.statistics_clicked.emit()
        
    def on_settings_clicked(self):
        self.settings_clicked.emit()
        
    def on_language_toggle(self):
        self.language_toggled.emit()
        
    def on_theme_toggle(self):
        self.theme_toggled.emit()
        
    def on_logout_clicked(self):
        self.logout_clicked.emit()