from PyQt5.QtWidgets import QLabel, QToolButton, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QBrush, QColor, QFont, QImage
from PyQt5.QtCore import QSize
from pathlib import Path
import os

class UserAvatar(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(36, 36)
        self.setStyleSheet("""
            QLabel {
                border-radius: 18px;
                background-color: transparent;
            }
        """)
        
    def load_avatar(self, username, user_data):
        """تحميل صورة المستخدم من بيانات المستخدم المخزنة أو إنشاء صورة افتراضية"""
        # استخراج مسار الصورة من بيانات المستخدم
        user_image_path = user_data.get("image", "") if user_data else ""

        if user_image_path and os.path.exists(user_image_path):
            # مسح ذاكرة التخزين المؤقت للصور
            from PyQt5.QtGui import QPixmapCache
            QPixmapCache.clear()
            
            # تحميل الصورة
            image = QImage(user_image_path)  
            if not image.isNull():
                pixmap = QPixmap.fromImage(image)
            else:
                pixmap = QPixmap(user_image_path)
        else:
            # إنشاء صورة افتراضية بالحرف الأول
            pixmap = self.create_avatar_image(username)

        # اقتصاص الصورة لتكون دائرية
        circular_pixmap = QPixmap(36, 36)
        circular_pixmap.fill(Qt.transparent)

        painter = QPainter(circular_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        scaled_pixmap = pixmap.scaled(36, 36, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        painter.setBrush(QBrush(scaled_pixmap))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, 36, 36)
        painter.end()

        # تطبيق الصورة وتحديث الواجهة فوراً
        self.setPixmap(circular_pixmap)
        self.update()
        
    def create_avatar_image(self, username):
        """إنشاء صورة افتراضية بالحرف الأول من اسم المستخدم"""
        size = 100  # حجم الصورة الأصلية
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        # اختيار لون خلفية عشوائي بناءً على اسم المستخدم
        colors = [
            "#3498db", "#2ecc71", "#9b59b6", "#e74c3c", "#f39c12",
            "#1abc9c", "#d35400", "#27ae60", "#8e44ad", "#c0392b"
        ]
        char_index = ord(username[0].upper()) if username else 0
        color_index = char_index % len(colors)
        bg_color = QColor(colors[color_index])
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # رسم خلفية دائرية
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, size, size)
        
        # إضافة الحرف الأول
        font = QFont("Arial", 48, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor("#ffffff"))
        
        # حساب موقع النص ليكون في المنتصف
        text = username[0].upper() if username else "U"
        text_rect = painter.boundingRect(pixmap.rect(), Qt.AlignCenter, text)
        x = (size - text_rect.width()) / 2
        y = (size - text_rect.height()) / 2 + text_rect.height() - text_rect.bottom()
        
        painter.drawText(int(x), int(y), text)
        painter.end()
        
        return pixmap


class AvatarButton(QToolButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("avatar_btn")
        self.setFixedSize(36, 36)
        self.setCursor(Qt.PointingHandCursor)
          
        # إضافة الصورة إلى الزر
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.avatar = UserAvatar()
        layout.addWidget(self.avatar)
        
    def set_user_data(self, username, user_data):
        """تعيين بيانات المستخدم وتحميل الصورة"""
        self.avatar.load_avatar(username, user_data)