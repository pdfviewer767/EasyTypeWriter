from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel
from PyQt5.QtGui import QPixmap, QIcon
from utils.resource import resource_path
from PyQt5.QtCore import Qt

class SignatureBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        # إعداد التصميم الأساسي للشريط
        self.setFixedHeight(40)
        self.setStyleSheet("""
            SignatureBar {
                background-color: #ec0ca9ff;
                border-top: 1px solid #bbdefb;
            }
        """)
        
        # إنشاء تخطيط أفقي
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(10)
        
        # إضافة أيقونة التطبيق
        icon_label = QLabel()
        icon_pixmap = QPixmap(resource_path("assets/icons/type.ico"))
        icon_label.setFixedSize(24, 24)
        if not icon_pixmap.isNull():
            icon_label.setPixmap(icon_pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(icon_label)
        
        # إضافة نص التوقيع
        signature_text = "هذا التطبيق وقف لله تعالى - تصميم م. رضا عباس"
        signature_label = QLabel(signature_text)
        signature_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;  background-color: #ec0ca9ff;")
        layout.addWidget(signature_label)
        signature_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # عكس وضع الكتابة

        # إضافة مساحة فارغة لدفع النص إلى اليمين
    def update_theme(self, is_dark):
            # Implement theme update logic here
            if is_dark:
                # Set dark theme properties
                self.setStyleSheet("background-color: #2b2b2b; color: white;")
            else:
                # Set light theme properties
                self.setStyleSheet("background-color: white; color: black;")