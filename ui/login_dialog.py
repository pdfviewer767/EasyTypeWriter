# login_dialog.py

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QMessageBox, QWidget, QComboBox, QScrollArea, QSizePolicy
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve,QSize
import os
import json
import hashlib
import binascii
import hmac
import re
import time
import base64
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from utils.tr import tr
from utils.resource import migrate_user_images, resource_path, user_data_directory, user_data_path

# تحديث المسارات لاستخدام resource_path
USERS_DIR = user_data_directory("data")
USERS_FILE = user_data_path(os.path.join("data", "users.json"))

# تعريف ثوابت المستخدم الإداري
ADMIN_USERNAME = "admin"
admin_image_path = ""  # أو مسار الصورة

ADMIN_ROLE = "مدير النظام"
profile_image_path = ""  # أو قيمة مسار افتراضية

# قائمة الأسئلة الأمنية
SECURITY_QUESTIONS = [
    "ما هو اسم مدرستك الابتدائية؟",
    "ما هو اسم حيوانك الأليف الأول؟",
    "ما هو اسم والدتك قبل الزواج؟",
    "ما هو أول هاتف محمول امتلكته؟",
    "ما هي المدينة التي ولدت فيها؟",
    "ما هو طعامك المفضل؟",
    "ما هو لقبك في المدرسة؟",
    "ما هو اسم أفضل صديق في الطفولة؟"
]

def generate_initial_admin_password():
    return secrets.token_urlsafe(18) + "!1a"


def is_account_locked(user, now=None):
    if not user.get("locked", False):
        return False

    try:
        locked_until = float(user.get("locked_until", 0))
    except (TypeError, ValueError):
        locked_until = 0

    if locked_until <= (time.time() if now is None else now):
        user["locked"] = False
        user["failed_attempts"] = 0
        user.pop("locked_until", None)
        return False
    return True


class ForgotPasswordDialog(QDialog):
    def __init__(self, users, encryption_key, parent=None):
        super().__init__(parent)
        self.users = users
        self.encryption_key = encryption_key
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle(tr("استعادة كلمة المرور"))
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        self.setLayout(layout)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("اسم المستخدم")
        layout.addWidget(QLabel("اسم المستخدم:"))
        layout.addWidget(self.username_input)
        
        self.find_user_btn = QPushButton("البحث عن المستخدم")
        self.find_user_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.find_user_btn)
        
        self.question1_label = QLabel("السؤال الأول:")
        self.answer1_input = QLineEdit()
        self.answer1_input.setPlaceholderText("الإجابة على السؤال الأول")
        
        self.question2_label = QLabel("السؤال الثاني:")
        self.answer2_input = QLineEdit()
        self.answer2_input.setPlaceholderText("الإجابة على السؤال الثاني")
        
        layout.addWidget(self.question1_label)
        layout.addWidget(self.answer1_input)
        layout.addWidget(self.question2_label)
        layout.addWidget(self.answer2_input)
        
        self.verify_btn = QPushButton("التحقق من الإجابات")
        self.verify_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.verify_btn)
        
        self.new_pass_label = QLabel("كلمة المرور الجديدة:")
        self.new_pass_input = QLineEdit()
        self.new_pass_input.setEchoMode(QLineEdit.Password)
        self.new_pass_input.setPlaceholderText("أدخل كلمة مرور جديدة")
        
        self.confirm_pass_label = QLabel("تأكيد كلمة المرور الجديدة:")
        self.confirm_pass_input = QLineEdit()
        self.confirm_pass_input.setEchoMode(QLineEdit.Password)
        self.confirm_pass_input.setPlaceholderText("أعد إدخال كلمة المرور الجديدة")
        
        self.change_pass_btn = QPushButton("تغيير كلمة المرور")
        self.change_pass_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px;
                border-radius: 5px;
            }
        """)
        
        # إخفاء حقول كلمة المرور الجديدة في البداية
        self.question1_label.hide()
        self.answer1_input.hide()
        self.question2_label.hide()
        self.answer2_input.hide()
        self.verify_btn.hide()
        self.new_pass_label.hide()
        self.new_pass_input.hide()
        self.confirm_pass_label.hide()
        self.confirm_pass_input.hide()
        self.change_pass_btn.hide()
        
        layout.addWidget(self.new_pass_label)
        layout.addWidget(self.new_pass_input)
        layout.addWidget(self.confirm_pass_label)
        layout.addWidget(self.confirm_pass_input)
        layout.addWidget(self.change_pass_btn)
        
        # الاتصالات
        self.find_user_btn.clicked.connect(self.find_user)
        self.verify_btn.clicked.connect(self.verify_answers)
        self.change_pass_btn.clicked.connect(self.change_password)
    
    def find_user(self):
        username = self.username_input.text().strip()
        if not username:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال اسم المستخدم.")
            return
        
        user = next((u for u in self.users if u.get("username") == username), None)
        if not user:
            QMessageBox.warning(self, "غير موجود", "اسم المستخدم غير موجود.")
            return
        
        self.current_user = user
        
        # فك تشفير الأسئلة والإجابات
        fernet = Fernet(self.encryption_key)
        
        try:
            # فك تشفير الأسئلة
            decrypted_question1 = fernet.decrypt(user["security_question1"].encode()).decode()
            decrypted_question2 = fernet.decrypt(user["security_question2"].encode()).decode()
            
            # عرض الأسئلة
            self.question1_label.setText(f"السؤال الأول: {decrypted_question1}")
            self.question2_label.setText(f"السؤال الثاني: {decrypted_question2}")
            
            # إظهار العناصر
            self.question1_label.show()
            self.answer1_input.show()
            self.question2_label.show()
            self.answer2_input.show()
            self.verify_btn.show()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في فك تشفير الأسئلة: {str(e)}")
    
    def verify_answers(self):
        answer1 = self.answer1_input.text().strip()
        answer2 = self.answer2_input.text().strip()
        
        if not answer1 or not answer2:
            QMessageBox.warning(self, "خطأ", "يرجى الإجابة على كلا السؤالين.")
            return
        
        fernet = Fernet(self.encryption_key)
        
        try:
            # فك تشفير الإجابات المخزنة
            decrypted_answer1 = fernet.decrypt(self.current_user["security_answer1"].encode()).decode()
            decrypted_answer2 = fernet.decrypt(self.current_user["security_answer2"].encode()).decode()
            
            # التحقق من الإجابات (دون مراعاة الحالة)
            if answer1.lower() == decrypted_answer1.lower() and answer2.lower() == decrypted_answer2.lower():
                # إظهار حقول تغيير كلمة المرور
                self.new_pass_label.show()
                self.new_pass_input.show()
                self.confirm_pass_label.show()
                self.confirm_pass_input.show()
                self.change_pass_btn.show()
                QMessageBox.information(self, "تم التحقق", "تم التحقق من هويتك بنجاح. يمكنك الآن تغيير كلمة المرور.")
            else:
                QMessageBox.warning(self, "إجابات غير صحيحة", "واحدة أو أكثر من الإجابات غير صحيحة.")
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في التحقق من الإجابات: {str(e)}")
    
    def change_password(self):
        new_pass = self.new_pass_input.text()
        confirm_pass = self.confirm_pass_input.text()
        
        if not new_pass or not confirm_pass:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال كلمة المرور الجديدة وتأكيدها.")
            return
        
        if new_pass != confirm_pass:
            QMessageBox.warning(self, "خطأ", "كلمتا المرور غير متطابقتين.")
            return
        
        # التحقق من قوة كلمة المرور
        if len(new_pass) < 8:
            QMessageBox.warning(self, "كلمة مرور ضعيفة", "كلمة المرور يجب أن تكون 8 أحرف على الأقل.")
            return
        
        if not (re.search(r"[A-Za-z]", new_pass) and 
                re.search(r"\d", new_pass) and 
                re.search(r"[!@#$%^&*(),.?\":{}|<>]", new_pass)):
            QMessageBox.warning(self, "كلمة مرور ضعيفة", 
                "كلمة المرور يجب أن تحتوي على حروف وأرقام ورمز خاص واحد على الأقل.")
            return
        
        # تحديث كلمة المرور للمستخدم
        hashed_password, salt = self.parent().hash_password(new_pass)
        self.current_user["password"] = hashed_password
        self.current_user["salt"] = salt
        
        # حفظ التغييرات في قاعدة البيانات
        if self.parent().save_users(self.users):
            QMessageBox.information(self, "تم التغيير", "تم تغيير كلمة المرور بنجاح.")
            self.accept()
        else:
            QMessageBox.critical(self, "خطأ", "حدث خطأ أثناء حفظ كلمة المرور الجديدة.")


class LoginDialog(QDialog):
    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        
        # تحديث مسارات الملفات
        self.settings_file = user_data_path("settings.json")
        self.encryption_key_file = user_data_path("encryption.key")
        
        # تهيئة المتغيرات
        self.username = None
        # إضافة متغير لتخزين بيانات المستخدم بالكامل
        self.user_data = None
        self.failed_attempts = 0
        self.lockout_time = None
        self.encryption_key = self.get_encryption_key()
        
        # تحديد الارتفاع الأساسي والارتفاع الموسع
        self.base_height = 700
        self.expanded_height = 800
        
        self.setup_ui()
        self.setup_connections()
        self.setup_security()
        self.init_data_dir()
        self.load_remembered_user()

    def setup_ui(self):
        self.setWindowTitle(tr("app_title", "EasyTypeWriter"))
        # تحديث مسار الأيقونة
        self.setWindowIcon(QIcon(resource_path("assets/icons/type.ico")))
        self.setMinimumWidth(450)
        self.setMinimumHeight(self.base_height)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f0f4f8, stop:1 #cfd9df);
            }
            QCheckBox {
                font-size: 14px;
            }
            QScrollArea {
                border: none;
            }
        """)
        
        # تعريف أنماط التصميم
        self.btn_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1976d2, stop:1 #64b5f6);
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 18px;
                padding: 10px 0;
                margin-bottom: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1565c0, stop:1 #42a5f5);
            }
        """
        
        self.input_style = """
            QLineEdit {
                border-radius: 14px;
                border: 1.5px solid #b0bec5;
                padding: 10px;
                font-size: 15px;
                background: #f8fafc;
            }
        """
        
        # التخطيط الرئيسي مع إمكانية التمرير
        self.scroll_widget = QWidget()
        self.scroll_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.layout = QVBoxLayout(self.scroll_widget)
        self.layout.setSpacing(18)
        self.layout.setContentsMargins(32, 32, 32, 32)
        
        # إضافة رسالة ترحيبية
        self.welcome_label = QLabel("<b style='font-size:20px;color:#1976d2;'>مرحباً بك في نظام تعلم الكتابة باللمس!</b>")
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setWordWrap(True)
        self.layout.addWidget(self.welcome_label)
        
        self.logo_label = QLabel("<b style='font-size:28px;color:#1976d2;'>لوحة الدخول</b>")
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.logo_label)

        # أزرار الوضع
        self.mode_btn_container = QWidget()
        self.mode_btn_layout = QVBoxLayout(self.mode_btn_container)
        self.mode_btn_layout.setSpacing(10)
        
        self.mode_btn_login = QPushButton("تسجيل الدخول")
        self.mode_btn_register = QPushButton("تسجيل مستخدم جديد")
        self.mode_btn_login.setStyleSheet(self.btn_style)
        self.mode_btn_register.setStyleSheet(self.btn_style)
        self.mode_btn_layout.addWidget(self.mode_btn_login)
        self.mode_btn_layout.addWidget(self.mode_btn_register)
        
        self.layout.addWidget(self.mode_btn_container)

        # عناصر واجهة تسجيل الدخول
        self.login_widget = QWidget()
        self.login_layout = QVBoxLayout(self.login_widget)
        self.login_layout.setSpacing(10)
        
        self.login_user_input = QLineEdit()
        self.login_user_input.setPlaceholderText("اسم المستخدم")
        self.login_user_input.setStyleSheet(self.input_style)
        self.login_layout.addWidget(self.login_user_input)
        
        self.login_pass_input = QLineEdit()
        self.login_pass_input.setPlaceholderText("كلمة المرور")
        self.login_pass_input.setEchoMode(QLineEdit.Password)
        self.login_pass_input.setStyleSheet(self.input_style)
        self.login_layout.addWidget(self.login_pass_input)
        
        # خيارات الحفظ
        self.remember_me_container = QWidget()
        self.remember_me_layout = QVBoxLayout(self.remember_me_container)
        self.remember_me_layout.setSpacing(5)
        
        self.remember_me_checkbox = QCheckBox("حفظ اسم المستخدم")
        self.remember_me_layout.addWidget(self.remember_me_checkbox)
        
        self.remember_password_checkbox = QCheckBox("حفظ كلمة المرور")
        self.remember_me_layout.addWidget(self.remember_password_checkbox)
        
        self.login_layout.addWidget(self.remember_me_container)
        
        self.show_pass_checkbox = QCheckBox("إظهار كلمة المرور")
        self.login_layout.addWidget(self.show_pass_checkbox)
        
        self.login_btn = QPushButton("دخول")
        self.login_btn.setStyleSheet(self.btn_style)
        self.login_layout.addWidget(self.login_btn)
        
        # زر استعادة كلمة المرور
        self.forgot_pass_btn = QPushButton("نسيت كلمة المرور؟")
        self.forgot_pass_btn.setStyleSheet("""
            QPushButton {
                color: #1976d2;
                background: transparent;
                border: none;
                font-size: 14px;
                text-decoration: underline;
                padding: 5px;
            }
            QPushButton:hover {
                color: #1565c0;
            }
        """)
        self.login_layout.addWidget(self.forgot_pass_btn)
        
        self.layout.addWidget(self.login_widget)

        # عناصر واجهة التسجيل
        self.register_widget = QWidget()
        self.register_layout = QVBoxLayout(self.register_widget)
        self.register_layout.setSpacing(10)
        
        # حقل الاسم الثلاثي
        self.reg_fullname_input = QLineEdit()
        self.reg_fullname_input.setPlaceholderText("الاسم الثلاثي (عربي/إنجليزي)")
        self.reg_fullname_input.setStyleSheet(self.input_style)
        self.register_layout.addWidget(self.reg_fullname_input)
        
        # حقل البريد الإلكتروني
        self.reg_email_input = QLineEdit()
        self.reg_email_input.setPlaceholderText("البريد الإلكتروني")
        self.reg_email_input.setStyleSheet(self.input_style)
        self.register_layout.addWidget(self.reg_email_input)
        
        self.reg_user_input = QLineEdit()
        self.reg_user_input.setPlaceholderText("اسم المستخدم")
        self.reg_user_input.setStyleSheet(self.input_style)
        self.register_layout.addWidget(self.reg_user_input)
        
        self.reg_pass_input = QLineEdit()
        self.reg_pass_input.setPlaceholderText("كلمة المرور")
        self.reg_pass_input.setEchoMode(QLineEdit.Password)
        self.reg_pass_input.setStyleSheet(self.input_style)
        self.register_layout.addWidget(self.reg_pass_input)
        
        self.reg_pass2_input = QLineEdit()
        self.reg_pass2_input.setPlaceholderText("تأكيد كلمة المرور")
        self.reg_pass2_input.setEchoMode(QLineEdit.Password)
        self.reg_pass2_input.setStyleSheet(self.input_style)
        self.register_layout.addWidget(self.reg_pass2_input)
        
        # إضافة الأسئلة الأمنية
        self.register_layout.addWidget(QLabel("<b>أسئلة أمنية لاستعادة كلمة المرور:</b>"))
        
        # السؤال الأول
        self.security_question1_label = QLabel("السؤال الأمني الأول:")
        self.register_layout.addWidget(self.security_question1_label)
        
        self.security_question1_combo = QComboBox()
        self.security_question1_combo.addItems(SECURITY_QUESTIONS)
        self.register_layout.addWidget(self.security_question1_combo)
        
        self.security_answer1_input = QLineEdit()
        self.security_answer1_input.setPlaceholderText("الإجابة على السؤال الأول")
        self.register_layout.addWidget(self.security_answer1_input)
        
        # السؤال الثاني
        self.security_question2_label = QLabel("السؤال الأمني الثاني:")
        self.register_layout.addWidget(self.security_question2_label)
        
        self.security_question2_combo = QComboBox()
        self.security_question2_combo.addItems(SECURITY_QUESTIONS)
        self.register_layout.addWidget(self.security_question2_combo)
        
        self.security_answer2_input = QLineEdit()
        self.security_answer2_input.setPlaceholderText("الإجابة على السؤال الثاني")
        self.register_layout.addWidget(self.security_answer2_input)
        
        self.terms_checkbox = QCheckBox("أوافق على شروط الاستخدام")
        self.register_layout.addWidget(self.terms_checkbox)
        
        self.register_btn = QPushButton("تسجيل")
        self.register_btn.setStyleSheet(self.btn_style)
        self.register_layout.addWidget(self.register_btn)
        
        self.layout.addWidget(self.register_widget)
        
        # تعيين التمرير
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_widget)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.scroll_area)
        
        # تهيئة الواجهة
        self.setMinimumHeight(self.base_height)
        self.login_widget.setVisible(True)
        self.register_widget.setVisible(False)

    def setup_connections(self):
        """تهيئة الاتصالات بين الإشارات والوظائف"""
        self.mode_btn_login.clicked.connect(self.show_login)
        self.mode_btn_register.clicked.connect(self.show_register)
        self.login_btn.clicked.connect(self.handle_login)
        self.register_btn.clicked.connect(self.handle_register)
        self.show_pass_checkbox.stateChanged.connect(self.toggle_password_visibility)
        self.remember_me_checkbox.stateChanged.connect(self.toggle_remember_password_enabled)
        self.forgot_pass_btn.clicked.connect(self.show_forgot_password_dialog)

    def show_forgot_password_dialog(self):
        """عرض نافذة استعادة كلمة المرور"""
        users = self.load_users()
        dialog = ForgotPasswordDialog(users, self.encryption_key, self)
        dialog.exec_()

    def toggle_remember_password_enabled(self, state):
        """تمكين/تعطيل خيار حفظ كلمة المرور حسب حالة حفظ اسم المستخدم"""
        self.remember_password_checkbox.setEnabled(state == Qt.Checked)
        if state != Qt.Checked:
            self.remember_password_checkbox.setChecked(False)

    def setup_security(self):
        """تهيئة نظام الأمان"""
        # مؤقت للأمان
        self.security_timer = QTimer(self)
        self.security_timer.timeout.connect(self.check_security)
        self.security_timer.start(1000)  # تحقق كل ثانية

        # إظهار واجهة تسجيل الدخول افتراضياً
        self.login_widget.setVisible(True)
        self.register_widget.setVisible(False)

    def load_remembered_user(self):
        """تحميل اسم المستخدم وكلمة المرور المحفوظة إن وجدت"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                username = settings.get('remembered_username', '')
                encrypted_password = settings.get('remembered_password', '')

                if username:
                    self.login_user_input.setText(username)
                    self.remember_me_checkbox.setChecked(True)
        
                    if encrypted_password:
                        try:
                            # فك تشفير كلمة المرور
                            fernet = Fernet(self.encryption_key)
                            password = fernet.decrypt(encrypted_password.encode()).decode()
                            self.login_pass_input.setText(password)
                            self.remember_password_checkbox.setChecked(True)
                        except Exception as e:
                            print(f"فك التشفير فشل: {str(e)}")
            else:
                # إنشاء ملف الإعدادات إذا لم يكن موجوداً
                with open(self.settings_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
        except Exception as e:
            print(f"خطأ في تحميل المستخدم المحفوظ: {str(e)}")

    def save_remembered_user(self, username, password):
        """حفظ اسم المستخدم وكلمة المرور للإستدعاء لاحقاً"""
        try:
            settings = {}
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            
            settings['remembered_username'] = username
            
            if password and self.remember_password_checkbox.isChecked():
                # تشفير كلمة المرور
                fernet = Fernet(self.encryption_key)
                encrypted_password = fernet.encrypt(password.encode()).decode()
                settings['remembered_password'] = encrypted_password
            else:
                # حذف كلمة المرور المحفوظة إذا لم يتم اختيار حفظها
                if 'remembered_password' in settings:
                    del settings['remembered_password']
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"خطأ في حفظ المستخدم المحفوظ: {str(e)}")

    def clear_remembered_user(self):
        """حذف اسم المستخدم وكلمة المرور المحفوظة"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                if 'remembered_username' in settings:
                    del settings['remembered_username']
                if 'remembered_password' in settings:
                    del settings['remembered_password']
                
                with open(self.settings_file, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"خطأ في حذف المستخدم المحفوظ: {str(e)}")

    def get_encryption_key(self):
        """إنشاء أو استرجاع مفتاح التشفير"""
        key_file = self.encryption_key_file
        
        if os.path.exists(key_file):
            # تحميل المفتاح الموجود
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # إنشاء مفتاح جديد وحفظه
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key

    def init_data_dir(self):
        """إنشاء مجلد آمن لحفظ بيانات المستخدمين في مجلد data داخل المشروع"""
        if not os.path.exists(USERS_DIR):
            try:
                os.makedirs(USERS_DIR, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"لا يمكن إنشاء مجلد البيانات: {str(e)}")
        # التأكد من وجود المستخدم الإداري
        self.ensure_admin_user()

    def ensure_admin_user(self):
        """التأكد من وجود المستخدم الإداري في النظام"""
        users = self.load_users()
        admin_exists = any(user.get("username") == ADMIN_USERNAME for user in users)
        
        if not admin_exists:
            # إنشاء المستخدم الإداري إذا لم يكن موجوداً
            initial_password = generate_initial_admin_password()
            hashed_password, salt = self.hash_password(initial_password)
            admin_user = {
                "username": ADMIN_USERNAME,
                "full_name": "مدير النظام",
                "email": "admin@example.com",
                "password": hashed_password,
                "image": admin_image_path if 'admin_image_path' in locals() else "",  # مسار صورة المدير أو فارغ
                "salt": salt,
                "role": ADMIN_ROLE,
                "active": True,
                "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                "last_login": None,
                "failed_attempts": 0,
                "locked": False,
                "is_admin": True,
                "permissions": {
                    "view_stats": True,
                    "manage_lessons": True,
                    "manage_users": True,
                    "upload_files": True,
                    "export_data": True,
                    "admin_panel": True
                }
            }

            # إضافة أسئلة أمنية افتراضية للمدير (يجب تغييرها لاحقاً)
            fernet = Fernet(self.encryption_key)
            encrypted_question1 = fernet.encrypt("ما هو اسم مدرستك الابتدائية؟".encode()).decode()
            answer1 = secrets.token_urlsafe(18)
            encrypted_answer1 = fernet.encrypt(answer1.encode()).decode()
            encrypted_question2 = fernet.encrypt("ما هو اسم حيوانك الأليف الأول؟".encode()).decode()
            answer2 = secrets.token_urlsafe(18)
            encrypted_answer2 = fernet.encrypt(answer2.encode()).decode()
            
            admin_user["security_question1"] = encrypted_question1
            admin_user["security_answer1"] = encrypted_answer1
            admin_user["security_question2"] = encrypted_question2
            admin_user["security_answer2"] = encrypted_answer2
            
            users.append(admin_user)
            self.save_users(users)
            
            # تحذير أمني (يظهر فقط عند أول تشغيل)
            QMessageBox.warning(self, "الحساب الإداري", 
                f"تم إنشاء حساب المدير\n"
                f"اسم المستخدم: {ADMIN_USERNAME}\n"
                f"كلمة المرور المؤقتة: {initial_password}\n"
                f"إجابة الاستعادة الأولى: {answer1}\n"
                f"إجابة الاستعادة الثانية: {answer2}\n\n"
                "احفظ هذه البيانات في مكان آمن؛ لن تظهر مرة أخرى.")

    def toggle_password_visibility(self, state):
        """تبديل إظهار/إخفاء كلمات المرور"""
        if state == Qt.Checked:
            self.login_pass_input.setEchoMode(QLineEdit.Normal)
            self.reg_pass_input.setEchoMode(QLineEdit.Normal)
            self.reg_pass2_input.setEchoMode(QLineEdit.Normal)
        else:
            self.login_pass_input.setEchoMode(QLineEdit.Password)
            self.reg_pass_input.setEchoMode(QLineEdit.Password)
            self.reg_pass2_input.setEchoMode(QLineEdit.Password)

    def show_login(self):
        # إظهار واجهة تسجيل الدخول وإخفاء التسجيل
        self.register_widget.setVisible(False)
        self.login_widget.setVisible(True)
        
        # إنشاء تأثير متحرك لتقليل حجم النافذة
        self.animate_height(self.base_height)

    def show_register(self):
        # إظهار واجهة التسجيل وإخفاء تسجيل الدخول
        self.login_widget.setVisible(False)
        self.register_widget.setVisible(True)
        
        # إنشاء تأثير متحرك لتكبير حجم النافذة
        self.animate_height(self.expanded_height)
        
        # تمرير إلى الأعلى لرؤية الحقول بوضوح
        QTimer.singleShot(700, lambda: self.scroll_area.verticalScrollBar().setValue(0))

    def animate_height(self, target_height):
        """تطبيق تأثير متحرك لتغيير ارتفاع النافذة"""
        animation = QPropertyAnimation(self, b"size")
        animation.setDuration(700)
        animation.setEasingCurve(QEasingCurve.OutQuad)
        animation.setStartValue(self.size())
        animation.setEndValue(QSize(self.size().width(), target_height))
        animation.start()

    def get_username(self):
        return self.username

    # إضافة دالة جديدة للحصول على بيانات المستخدم الكاملة
    def get_user_data(self):
        """الحصول على بيانات المستخدم المسجل الدخول"""
        return self.user_data

    def hash_password(self, password, salt=None):
        """تجزئة كلمة المرور باستخدام خوارزمية PBKDF2 مع ملح فريد"""
        if salt is None:
            salt = os.urandom(16)  # توليد ملح عشوائي 16 بايت
        else:
            salt = binascii.unhexlify(salt)
        
        # استخدام 100,000 تكرار لزيادة الأمان ضد الهجمات
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000,
            dklen=32
        )
        return binascii.hexlify(key).decode('ascii'), binascii.hexlify(salt).decode('ascii')

    def verify_password(self, stored_password, salt, provided_password):
        """التحقق من تطابق كلمة المرور مع التجزئة المخزنة"""
        key_hex, _ = self.hash_password(provided_password, salt)
        return hmac.compare_digest(key_hex, stored_password)

    def load_users(self):
        """تحميل بيانات المستخدمين من الملف الموحد"""
        if not os.path.exists(USERS_FILE):
            return []
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                users_list = data
            elif isinstance(data, dict):
                users_dict = data.get("users", {})
                users_list = list(users_dict.values()) if isinstance(users_dict, dict) else users_dict
            else:
                users_list = []
            users = [user for user in users_list if isinstance(user, dict)]
            if migrate_user_images(users):
                self.save_users(users)
            return users
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل بيانات المستخدمين: {str(e)}")
            return []

    def save_users(self, users):
        """حفظ بيانات المستخدمين في الملف الموحد"""
        try:
            # تحويل قائمة المستخدمين إلى dict مع اسم المستخدم كمفتاح
            data = {"users": {user["username"]: user for user in users}}
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في حفظ بيانات المستخدمين: {str(e)}")
            return False


    def check_security(self):
        """التحقق من إجراءات الأمان (مثل فترة الحظر)"""
        if self.lockout_time:
            remaining = self.lockout_time - time.time()
            if remaining > 0:
                self.login_btn.setEnabled(False)
                self.login_btn.setText(f"جرب بعد {int(remaining)} ثانية")
            else:
                self.lockout_time = None
                self.login_btn.setEnabled(True)
                self.login_btn.setText("دخول")
                self.failed_attempts = 0

    def handle_login(self):
        """معالجة عملية تسجيل الدخول"""
        if self.lockout_time:
            QMessageBox.warning(self, "حساب مؤقت", "حسابك مؤقتاً. الرجاء الانتظار قبل المحاولة مرة أخرى.")
            return
        
        username = self.login_user_input.text().strip()
        password = self.login_pass_input.text()
        
        # التحقق من الحقول المطلوبة
        if not username or not password:
            QMessageBox.warning(self, "حقول ناقصة", "يرجى إدخال اسم المستخدم وكلمة المرور.")
            return
        
        users = self.load_users()
        user = next((u for u in users if u.get("username") == username), None)
        
        # التحقق من وجود المستخدم
        if not user:
            QMessageBox.warning(self, "مستخدم غير موجود", "اسم المستخدم غير موجود. يرجى التسجيل أولاً.")
            return
        
        if not user.get("active", True):
            QMessageBox.warning(self, "حساب معطل", "تم تعطيل هذا الحساب. تواصل مع مدير النظام.")
            return

        if not user.get("is_admin", False) and is_account_locked(user):
            QMessageBox.warning(self, "حساب مقفل", "حسابك مقفل مؤقتاً. حاول مرة أخرى بعد انتهاء المهلة.")
            return
        
        # التحقق من كلمة المرور
        if self.verify_password(user["password"], user["salt"], password):
            user["failed_attempts"] = 0
            user["locked"] = False
            user.pop("locked_until", None)
            user["last_login"] = time.strftime("%Y-%m-%d %H:%M:%S")
            self.save_users(users)
            # تخزين بيانات المستخدم الكاملة
            self.user_data = user
            self.username = username
            self.is_admin = user.get("is_admin", False)
            
            # حفظ أو حذف معلومات المستخدم حسب حالة المربعات
            if self.remember_me_checkbox.isChecked():
                self.save_remembered_user(username, password)
            else:
                self.clear_remembered_user()
                
            self.accept()
            # إعادة تعيين محاولات الفشل بعد تسجيل الدخول الناجح
            self.failed_attempts = 0
        else:
            self.failed_attempts = int(user.get("failed_attempts", 0)) + 1
            user["failed_attempts"] = self.failed_attempts
            remaining_attempts = 5 - self.failed_attempts
            
            if remaining_attempts > 0:
                self.save_users(users)
                QMessageBox.warning(self, "كلمة مرور خاطئة", 
                    f"كلمة المرور غير صحيحة. لديك {remaining_attempts} محاولات متبقية.")
            else:
                # قفل الحساب لمدة 5 دقائق بعد 5 محاولات فاشلة (لا ينطبق على المدير)
                if not user.get("is_admin", False):
                    self.lockout_time = time.time() + 300  # 5 دقائق
                    user["locked"] = True
                    user["locked_until"] = self.lockout_time
                    self.save_users(users)
                    QMessageBox.warning(self, "حساب مؤقت", 
                        "تم تجاوز عدد المحاولات المسموحة. تم تعليق الحساب لمدة 5 دقائق.")
                else:
                    self.save_users(users)
                    QMessageBox.warning(self, "تحذير أمني", 
                        "تم تجاوز عدد المحاولات المسموحة للحساب الإداري!")

    def handle_register(self):
        """معالجة عملية تسجيل مستخدم جديد"""
        fullname = self.reg_fullname_input.text().strip()
        email = self.reg_email_input.text().strip().lower()
        username = self.reg_user_input.text().strip()
        password = self.reg_pass_input.text()
        password2 = self.reg_pass2_input.text()
        
        # الحصول على الأسئلة الأمنية والإجابات
        question1 = self.security_question1_combo.currentText()
        answer1 = self.security_answer1_input.text().strip()
        question2 = self.security_question2_combo.currentText()
        answer2 = self.security_answer2_input.text().strip()
        
        # التحقق من الحقول المطلوبة
        if not fullname or not email or not username or not password or not password2:
            QMessageBox.warning(self, "حقول ناقصة", "يرجى إدخال جميع الحقول المطلوبة.")
            return
        
        # التحقق من الأسئلة الأمنية
        if not question1 or not question2:
            QMessageBox.warning(self, "أسئلة أمنية", "يرجى اختيار سؤالين أمنيين.")
            return
            
        if not answer1 or not answer2:
            QMessageBox.warning(self, "إجابات أمنية", "يرجى الإجابة على كلا السؤالين الأمنيين.")
            return
            
        if question1 == question2:
            QMessageBox.warning(self, "أسئلة مكررة", "يرجى اختيار سؤالين مختلفين.")
            return
        
        # منع تسجيل مستخدم باسم "admin"
        if username.lower() == ADMIN_USERNAME:
            QMessageBox.warning(self, "اسم محجوز", "اسم المستخدم 'admin' محجوز للنظام.")
            return
        
        # التحقق من قبول شروط الاستخدام
        if not self.terms_checkbox.isChecked():
            QMessageBox.warning(self, "شروط الاستخدام", "يجب الموافقة على شروط الاستخدام.")
            return
        
        # التحقق من صحة الاسم الثلاثي
        if not re.match(r"^[\u0600-\u06FFa-zA-Z\s]{3,50}$", fullname):
            QMessageBox.warning(self, "اسم غير صالح", 
                "الاسم الثلاثي يجب أن يكون بين 3-50 حرفاً ويحتوي فقط على أحرف عربية أو إنجليزية.")
            return
        
        # التحقق من صحة البريد الإلكتروني
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            QMessageBox.warning(self, "بريد إلكتروني غير صالح", "يرجى إدخال بريد إلكتروني صالح.")
            return
        
        # التحقق من صحة اسم المستخدم
        if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
            QMessageBox.warning(self, "اسم مستخدم غير صالح", 
                "اسم المستخدم يجب أن يكون بين 3-20 حرفاً ويحتوي فقط على أحرف إنجليزية وأرقام وشرطات سفلية.")
            return
        
        # التحقق من قوة كلمة المرور
        if len(password) < 8:
            QMessageBox.warning(self, "كلمة مرور ضعيفة", "كلمة المرور يجب أن تكون 8 أحرف على الأقل.")
            return
        
        if not (re.search(r"[A-Za-z]", password) and 
                re.search(r"\d", password) and 
                re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)):
            QMessageBox.warning(self, "كلمة مرور ضعيفة", 
                "كلمة المرور يجب أن تحتوي على حروف وأرقام ورمز خاص واحد على الأقل.")
            return
        
        # التحقق من تطابق كلمتي المرور
        if password != password2:
            QMessageBox.warning(self, "كلمتا مرور غير متطابقتين", "كلمتا المرور غير متطابقتين. يرجى التأكد.")
            return
        
        users = self.load_users()
        
        # التحقق من عدم وجود اسم المستخدم مسبقاً
        if any(u.get("username") == username for u in users):
            QMessageBox.warning(self, "اسم مستخدم موجود", "اسم المستخدم موجود بالفعل. اختر اسمًا آخر.")
            return
        
        # التحقق من عدم وجود البريد الإلكتروني مسبقاً
        if any(u.get("email") == email for u in users):
            QMessageBox.warning(self, "بريد إلكتروني مستخدم", "البريد الإلكتروني مستخدم بالفعل. اختر بريداً آخر.")
            return
        
        # تجزئة كلمة المرور
        hashed_password, salt = self.hash_password(password)
        
        # تشفير الأسئلة الأمنية والإجابات
        fernet = Fernet(self.encryption_key)
        encrypted_question1 = fernet.encrypt(question1.encode()).decode()
        encrypted_answer1 = fernet.encrypt(answer1.encode()).decode()
        encrypted_question2 = fernet.encrypt(question2.encode()).decode()
        encrypted_answer2 = fernet.encrypt(answer2.encode()).decode()
        
        # إنشاء المستخدم الجديد (بدون صلاحيات المدير)
        new_user = {
            "username": username,
            "full_name": fullname,
            "email": email,
            "password": hashed_password,
            "image": "",  # تأكد من تعيين هذا كسلسلة فارغة
            "salt": salt,
            "role": "طالب",
            "active": True,
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": None,
            "failed_attempts": 0,
            "locked": False,
            "is_admin": False,
            "security_question1": encrypted_question1,
            "security_answer1": encrypted_answer1,
            "security_question2": encrypted_question2,
            "security_answer2": encrypted_answer2,
            "permissions": {
                "view_stats": True,
                "manage_lessons": False,
                "manage_users": False,
                "upload_files": False,
                "export_data": False,
                "admin_panel": False
            }
        }
        
        # إضافة المستخدم وحفظ البيانات
        users.append(new_user)
        if self.save_users(users):
            # تخزين بيانات المستخدم الجديد لتسجيل الدخول التلقائي
            self.user_data = new_user
            self.accept()
            QMessageBox.information(self, "تم التسجيل", 
                "تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول.")
        else:
            QMessageBox.critical(self, "خطأ", "حدث خطأ أثناء حفظ بيانات المستخدم.")