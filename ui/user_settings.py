# user_settings.py
# شاشة إعدادات المستخدم في التطبيق
from PyQt5.QtWidgets import (
    QWidget, QListWidget, QStackedWidget, QHBoxLayout, QListWidgetItem,
    QFormLayout, QLineEdit, QComboBox, QPushButton, QCheckBox, 
    QFileDialog, QLabel, QMessageBox, QMainWindow, QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QRegExp
from PyQt5.QtGui import QPixmap, QImage, QRegExpValidator, QMouseEvent
import os
import shutil
import json
import re
from datetime import datetime
from utils.tr import tr
from utils.resource import resource_path, user_data_directory, user_data_path


class ClickableLabel(QLabel):
    """تسمح QLabel بأن ترصد حدث النقر"""
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)  # تغيير شكل المؤشر عند المرور

    def mouseReleaseEvent(self, ev: QMouseEvent):
        if ev.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(ev)


class UserSettingsWindow(QWidget):
    # إشارة لتحديث الصورة في أيقونة المستخدم
    profile_image_updated = pyqtSignal(str)
    
    def __init__(self, settings=None, language='ar', username=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.language = language
        self.username = username
        self.image_path = ""
        self.data_folder = user_data_directory("data")
        self.users_file = user_data_path(os.path.join("data", "users.json"))
        self.user_images_folder = user_data_directory("data", "user_images")
        
        # إنشاء المجلدات إذا لم تكن موجودة
        os.makedirs(self.data_folder, exist_ok=True)
        os.makedirs(self.user_images_folder, exist_ok=True)
        
        self.setMinimumSize(800, 500)
        self.sections = {}

        self.init_ui()
        self.update_texts()
        self.load_user_data()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(250)
        self.sidebar.setStyleSheet("QListWidget { border: none; font-size: 16px; }")
        self.sidebar.itemClicked.connect(self.display_section)
        main_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, 1)

        self.personal_section = self.create_personal_section()
        self.stack.addWidget(self.personal_section)

        self.setLayout(main_layout)

    def update_texts(self):
        self.setWindowTitle(tr("user_settings_title"))

        self.sections = {
            "personal": tr("personal_info"),
        }
        self.sidebar.clear()
        for key, label in self.sections.items():
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, key)
            self.sidebar.addItem(item)
        self.update_personal_texts()
        self.update_form_labels()  # تحديث تسميات النموذج
        self.stack.setCurrentIndex(0)
        self.setLayoutDirection(Qt.RightToLeft if self.language == 'ar' else Qt.LeftToRight)

    def display_section(self, item):
        key = item.data(Qt.UserRole)
        index = list(self.sections.keys()).index(key)
        self.stack.setCurrentIndex(index)
    def update_form_labels(self):
        """تحديث تسميات النموذج عند تغيير اللغة"""
        # تحديث تسميات الحقول
        self.full_name_label.setText(tr("✏️ full_name"))
        self.email_label.setText(tr("📧 email"))
        self.current_password_label.setText(tr("🔑 current_password"))
        self.new_password_label.setText(tr("🔑 new_password"))
        self.confirm_password_label.setText(tr("confirm_password"))
        
    # تحديث نصوص الأزرار
        self.save_btn.setText(tr("save_data"))

    def create_personal_section(self): 
        widget = QWidget()
        self.layout = QFormLayout()  # جعل التخطيط متغيرًا على مستوى الفئة

        # حقل الاسم الكامل (للقراءة فقط)
        self.full_name_edit = QLineEdit()
        self.full_name_edit.setReadOnly(True)

        # حقل البريد الإلكتروني (للقراءة فقط)
        self.email_edit = QLineEdit()
        self.email_edit.setReadOnly(True)

        # حقل كلمة المرور الحالية
        self.current_password_edit = QLineEdit()
        self.current_password_edit.setEchoMode(QLineEdit.Password)
        
        # حقل كلمة المرور الجديدة
        self.new_password_edit = QLineEdit()
        self.new_password_edit.setEchoMode(QLineEdit.Password)
        
        # حقل تأكيد كلمة المرور الجديدة
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.Password)
        
        # زر حفظ البيانات (تعريفه هنا)
        self.save_btn = QPushButton()
        self.save_btn.clicked.connect(self.save_text_data)
        
        # مكان عرض الصورة (تفاعلية)
        self.avatar_label = ClickableLabel()
        self.avatar_label.setFixedSize(100, 100)
        self.avatar_label.setStyleSheet("""
            border: 1px solid #ccc;
            border-radius: 50px;
            background-color: #f0f0f0;
        """)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setToolTip(tr("click_to_change_image"))  # تلميح عند المرور
        
        # ربط الضغط على الصورة بفتح نافذة اختيار صورة جديدة
        self.avatar_label.clicked.connect(self.upload_image)
        
        # إنشاء تسميات الحقول
        self.profile_image_label = QLabel()
        self.full_name_label = QLabel()
        self.email_label = QLabel()
        self.current_password_label = QLabel()
        self.new_password_label = QLabel()
        self.confirm_password_label = QLabel()
        
        # إضافة العناصر إلى التخطيط
        self.layout.addRow(self.profile_image_label, self.avatar_label)
        self.layout.addRow(self.full_name_label, self.full_name_edit)
        self.layout.addRow(self.email_label, self.email_edit)
        self.layout.addRow(self.current_password_label, self.current_password_edit)
        self.layout.addRow(self.new_password_label, self.new_password_edit)
        self.layout.addRow(self.confirm_password_label, self.confirm_password_edit)
        self.layout.addRow("", self.save_btn)

        widget.setLayout(self.layout)
        return widget

        def update_form_labels(self):
            """تحديث تسميات النموذج عند تغيير اللغة"""
            # تحديث تسميات الحقول
            self.full_name_label.setText(tr("✏️ full_name"))
            self.email_label.setText(tr("📧 email"))
            self.current_password_label.setText(tr("🔑 current_password"))
            self.new_password_label.setText(tr("🔑 new_password"))
            self.confirm_password_label.setText(tr("confirm_password"))
            
            # تحديث نص زر الحفظ فقط (زر رفع الصورة أُزيل)
            self.save_btn.setText(tr("save_data"))

    def update_personal_texts(self):
        self.full_name_edit.setPlaceholderText(tr("full_name_placeholder"))
        self.email_edit.setPlaceholderText(tr("email_placeholder"))
        self.current_password_edit.setPlaceholderText(tr("current_password_placeholder"))
        self.new_password_edit.setPlaceholderText(tr("new_password_placeholder"))
        self.confirm_password_edit.setPlaceholderText(tr("confirm_password_placeholder"))

    def upload_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            tr("select_profile_image"),
            "",
            tr("image_files") + " (*.png *.jpg *.jpeg)"
        )
        
        if file_path:
            try:
                # جلب بيانات المستخدم لمعرفة الصورة القديمة
                user_data = self.get_user_data()
                old_image_path = user_data.get("image", "") if user_data else ""
                
                # حذف الصورة القديمة إذا كانت موجودة
                self.delete_old_image(old_image_path)
                
                # توليد اسم فريد للصورة
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"{self.username}_{timestamp}{os.path.splitext(file_path)[1]}"
                save_path = os.path.join(self.user_images_folder, filename)
                
                # نسخ الصورة للمجلد الجديد
                shutil.copyfile(file_path, save_path)
                self.image_path = save_path
                
                # حل مشكلة تحذير ICC
                image = QImage(file_path)
                if not image.isNull():
                    pixmap = QPixmap.fromImage(image)
                else:
                    pixmap = QPixmap(file_path)
                    
                self.avatar_label.setPixmap(pixmap.scaled(
                    self.avatar_label.width(),
                    self.avatar_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                ))
                    
                # حفظ مسار الصورة الجديدة في ملف JSON
                self.save_image_path()
                
                # إرسال إشارة بتحديث الصورة مع المسار الجديد
                self.profile_image_updated.emit(self.image_path)
                
                QMessageBox.information(self, tr("upload_success"), tr("image_uploaded_successfully"))
            except Exception as e:
                QMessageBox.critical(self, tr("error"), tr("image_upload_error").format(error=str(e)))

    def delete_old_image(self, old_image_path):
        """حذف الصورة القديمة من المجلد إذا كانت موجودة"""
        if old_image_path and os.path.exists(old_image_path):
            try:
                os.remove(old_image_path)
                print(f"تم حذف الصورة القديمة: {old_image_path}")
            except Exception as e:
                print(f"خطأ أثناء حذف الصورة القديمة: {str(e)}")
                QMessageBox.warning(self, tr("warning"), 
                    tr("old_image_deletion_error").format(error=str(e)))

    def get_user_data(self):
        """استرجاع بيانات المستخدم من ملف JSON"""
        if not os.path.exists(self.users_file):
            return {}
            
        try:
            with open(self.users_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # التعامل مع البنية القديمة والجديدة
            if isinstance(data, list):
                for user in data:
                    if isinstance(user, dict) and user.get("username") == self.username:
                        return user
                return {}
            else:
                return data.get("users", {}).get(self.username, {})
                
        except Exception as e:
            print(f"خطأ في تحميل بيانات المستخدم: {str(e)}")
            return {}

    def save_image_path(self):
        """حفظ مسار الصورة في ملف JSON"""
        if not self.username or not self.image_path:
            return
            
        try:
            # تحميل البيانات الحالية
            if os.path.exists(self.users_file):
                with open(self.users_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
                
            # تحويل البنية القديمة إلى الجديدة إذا لزم الأمر
            if isinstance(data, list):
                new_data = {"users": {}}
                for user in data:
                    if isinstance(user, dict) and "username" in user:
                        username = user["username"]
                        new_data["users"][username] = user
                data = new_data
            
            # التأكد من وجود مفتاح "users"
            if "users" not in data:
                data["users"] = {}
                
            # تحديث مسار الصورة للمستخدم
            user_data = data["users"].get(self.username, {})
            user_data["image"] = self.image_path
            
            # حفظ التحديثات
            data["users"][self.username] = user_data
            
            # حفظ البيانات المحدثة
            with open(self.users_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            QMessageBox.critical(self, tr("error"), tr("image_path_save_error").format(error=str(e)))

    
    def validate_password(self):
        """التحقق من صحة كلمة المرور"""
        current_password = self.current_password_edit.text()
        new_password = self.new_password_edit.text()
        confirm_password = self.confirm_password_edit.text()
        
        # التحقق من إدخال كلمة المرور الحالية
        if not current_password:
            QMessageBox.warning(self, tr("validation_error"), tr("current_password_required"))
            return False
            
        # التحقق من صحة كلمة المرور الحالية
        user_data = self.get_user_data()
        if user_data:
            # التحقق من كلمة المرور الحالية
            if not self.parent().verify_password(user_data["password"], user_data["salt"], current_password):
                QMessageBox.warning(self, tr("validation_error"), tr("current_password_incorrect"))
                return False
        
        # التحقق من كلمة المرور الجديدة
        if not new_password:
            QMessageBox.warning(self, tr("validation_error"), tr("new_password_required"))
            return False
            
        # التحقق من تأكيد كلمة المرور
        if not confirm_password:
            QMessageBox.warning(self, tr("validation_error"), tr("confirm_password_required"))
            return False
            
        # التحقق من تطابق كلمتي المرور
        if new_password != confirm_password:
            QMessageBox.warning(self, tr("validation_error"), tr("passwords_not_match"))
            return False
            
        # التحقق من قوة كلمة المرور الجديدة
        if len(new_password) < 8:
            QMessageBox.warning(self, tr("validation_error"), tr("password_too_short"))
            return False
            
        if not (re.search(r"[A-Za-z]", new_password) and 
                re.search(r"\d", new_password) and 
                re.search(r"[!@#$%^&*(),.?\":{}|<>]", new_password)):
            QMessageBox.warning(self, tr("validation_error"), tr("password_weak"))
            return False
            
        return True
    
    def save_text_data(self):
        """حفظ البيانات (كلمة المرور فقط)"""
        if not self.username:
            QMessageBox.warning(self, tr("error"), tr("no_user_selected"))
            return
            
        # التحقق من صحة كلمة المرور
        if not self.validate_password():
            return
            
        try:
            # تحميل البيانات الحالية من الملف
            if os.path.exists(self.users_file):
                with open(self.users_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
                
            # إذا كانت البيانات على شكل قائمة (البنية القديمة)
            if isinstance(data, list):
                # تحويل البنية القديمة إلى الجديدة
                new_data = {"users": {}}
                for user in data:
                    if isinstance(user, dict) and "username" in user:
                        username = user["username"]
                        new_data["users"][username] = user
                data = new_data
            
            # التأكد من وجود مفتاح "users" في البيانات
            if "users" not in data:
                data["users"] = {}
                
            # تحديث كلمة المرور للمستخدم الحالي فقط
            user_data = data["users"].get(self.username, {})
            new_password = self.new_password_edit.text()
            hashed_password, salt = self.parent().hash_password(new_password)
            user_data["password"] = hashed_password
            user_data["salt"] = salt
            
            # حفظ التحديثات
            data["users"][self.username] = user_data
            
            # حفظ البيانات المحدثة
            with open(self.users_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            # مسح حقول كلمة المرور
            self.current_password_edit.clear()
            self.new_password_edit.clear()
            self.confirm_password_edit.clear()
                
            QMessageBox.information(self, tr("success"), tr("password_updated"))
        except Exception as e:
            QMessageBox.critical(self, tr("error"), tr("password_update_error").format(error=str(e)))


    def load_user_data(self):
        if not self.username:
            return
            
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # إذا كانت البيانات على شكل قائمة (البنية القديمة)
                if isinstance(data, list):
                    # البحث عن بيانات المستخدم في القائمة
                    user_data = {}
                    for user in data:
                        if isinstance(user, dict) and user.get("username") == self.username:
                            user_data = user
                            break
                else:
                    # البيانات على شكل قاموس (البنية الجديدة)
                    user_data = data.get("users", {}).get(self.username, {})
                
                # تحميل البيانات في الواجهة
                if user_data:
                    self.full_name_edit.setText(user_data.get("full_name", ""))
                    self.email_edit.setText(user_data.get("email", ""))
                    
                    image_path = user_data.get("image", "")
                    if image_path and os.path.exists(image_path):
                        self.image_path = image_path
                        # حل مشكلة تحذير ICC
                        image = QImage(image_path)
                        if not image.isNull():
                            pixmap = QPixmap.fromImage(image)
                        else:
                            pixmap = QPixmap(image_path)
                            
                        self.avatar_label.setPixmap(pixmap.scaled(
                            self.avatar_label.width(),
                            self.avatar_label.height(),
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        ))
        except Exception as e:
            print(f"Error loading user data: {e}")

    def on_language_changed(self, index):
        self.language = 'ar' if index == 0 else 'en'
        self.update_texts()
        
    def update_language(self, new_lang):
        self.language = new_lang
        self.update_texts()
