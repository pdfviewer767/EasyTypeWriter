# statistics_tab.py
# شاشة الإحصائيات في التطبيق
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QPixmap, QPainter, QColor, QLinearGradient, QBrush, QPen, QFont
from PyQt5.QtCore import Qt
import math
from utils.tr import tr
from utils.resource import resource_path  # تأكد من أن utils/resource.py موجود

class StatisticsTab(QWidget):
    def __init__(self, progress, language, lesson_keys, parent=None):
        super().__init__(parent)
        self.progress = progress
        self.language = language
        self.lesson_keys = lesson_keys
        
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)
        self.setLayout(self.layout)
        
        # محاولة تحميل ملف التنسيقات (اختياري)
        try:
            style_path = resource_path("styles/app.qss")
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"تعذر تحميل ملف التنسيقات: {e}")
        
        # عنوان الإحصائيات
        self.title_label = QLabel(tr("statistics"))
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #1976d2;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title_label)
        
        # مؤشر التقدم الرئيسي (على شكل عداد)
        self.progress_gauge = QLabel()
        self.progress_gauge.setFixedSize(300, 300)
        self.layout.addWidget(self.progress_gauge, alignment=Qt.AlignCenter)
        
        # تفاصيل الإحصائيات
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(10)
        
        self.completed_label = QLabel()
        stats_layout.addWidget(self.completed_label)
        
        self.recent_label = QLabel()
        stats_layout.addWidget(self.recent_label)
        
        self.level_label = QLabel()
        stats_layout.addWidget(self.level_label)
        
        self.speed_label = QLabel()
        stats_layout.addWidget(self.speed_label)
        
        self.accuracy_label = QLabel()
        stats_layout.addWidget(self.accuracy_label)
        
        self.top_speed_label = QLabel()
        stats_layout.addWidget(self.top_speed_label)
        
        self.total_time_label = QLabel()
        stats_layout.addWidget(self.total_time_label)
        
        self.layout.addLayout(stats_layout)
        
        # تحديث النصوص والقيم في البداية
        self.update_progress(self.progress, self.language, self.lesson_keys)
    
    def update_texts(self):
        # تحديث النصوص عند تغيير اللغة (مثلاً عند تبديل اللغة)
        self.title_label.setText(tr("statistics"))
        
        # لإعادة تحديث النصوص مع القيم الحالية
        self.update_progress(self.progress, self.language, self.lesson_keys)
    
    def update_progress(self, progress, language, lesson_keys):
        self.progress = progress
        self.language = language
        self.lesson_keys = lesson_keys
        
        # حساب التقدم
        completed_key = f"completed_lessons_{self.language}"
        completed_lessons = self.progress.get(completed_key, [])
        total_lessons = len(self.lesson_keys)
        progress_percent = (len(completed_lessons) / total_lessons * 100) if total_lessons > 0 else 0
        
        # تحديث نصوص الإحصائيات مع القيم
        self.completed_label.setText(
            f"{tr('completed_lessons')}: {len(completed_lessons)}/{total_lessons}"
        )
        
        last_lesson = completed_lessons[-1] if completed_lessons else tr('none')
        self.recent_label.setText(
            f"{tr('last_lesson')}: {last_lesson}"
        )
        
        # تحديد مستوى المستخدم
        if progress_percent < 30:
            level = tr('beginner')
        elif progress_percent < 70:
            level = tr('intermediate')
        else:
            level = tr('advanced')
        self.level_label.setText(
            f"{tr('your_level')}: {level}"
        )
        
        # جمع إحصائيات الجلسات
        total_speed = 0
        total_accuracy = 0
        top_speed = 0
        total_time = 0
        session_count = 0
        
        lang_sessions = self.progress.get(f"sessions_{self.language}", [])
        for session in lang_sessions:
            total_speed += session.get("wpm", 0)
            total_accuracy += session.get("accuracy", 0)
            top_speed = max(top_speed, session.get("wpm", 0))
            total_time += session.get("duration_seconds", 0)
            session_count += 1
        
        practice_sessions = self.progress.get("practice_sessions", [])
        for session in practice_sessions:
            total_speed += session.get("wpm", 0)
            total_accuracy += session.get("accuracy", 0)
            top_speed = max(top_speed, session.get("wpm", 0))
            total_time += session.get("duration_seconds", 0)
            session_count += 1
        
        avg_speed = total_speed / session_count if session_count > 0 else 0
        avg_accuracy = total_accuracy / session_count if session_count > 0 else 0
        
        hours = total_time // 3600
        minutes = (total_time % 3600) // 60
        
        self.speed_label.setText(
            f"{tr('avg_speed')}: {avg_speed:.1f} {tr('wpm')}"
        )
        self.accuracy_label.setText(
            f"{tr('avg_accuracy')}: {avg_accuracy:.1f}%"
        )
        self.top_speed_label.setText(
            f"{tr('top_speed')}: {top_speed} {tr('wpm')}"
        )
        self.total_time_label.setText(
            f"{tr('total_time')}: {hours}h {minutes}m"
        )
        
        self.update_gauge(progress_percent)
    
    def update_gauge(self, progress):
        """رسم مؤشر التقدم على شكل عداد"""
        pixmap = QPixmap(self.progress_gauge.size())
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.setPen(Qt.NoPen)
        
        rect = pixmap.rect().adjusted(10, 10, -10, -10)
        start_angle = 30 * 16
        span_angle = -240 * 16
        
        # خلفية العداد
        bg_gradient = QLinearGradient(rect.center().x(), rect.top(), rect.center().x(), rect.bottom())
        bg_gradient.setColorAt(0, QColor(240, 240, 240))
        bg_gradient.setColorAt(1, QColor(220, 220, 220))
        painter.setBrush(QBrush(bg_gradient))
        painter.drawPie(rect, start_angle, span_angle)
        
        # مؤشر التقدم
        progress_angle = int(span_angle * progress / 100)
        progress_gradient = QLinearGradient(rect.center().x(), rect.top(), rect.center().x(), rect.bottom())
        
        if progress < 33:
            color1 = QColor(255, 87, 87)
            color2 = QColor(198, 40, 40)
        elif progress < 66:
            color1 = QColor(255, 202, 40)
            color2 = QColor(230, 180, 30)
        else:
            color1 = QColor(76, 175, 80)
            color2 = QColor(56, 142, 60)
        
        progress_gradient.setColorAt(0, color1)
        progress_gradient.setColorAt(1, color2)
        painter.setBrush(QBrush(progress_gradient))
        painter.drawPie(rect, start_angle, progress_angle)
        
        # الإبرة
        needle_angle = start_angle + progress_angle
        angle_rad = (needle_angle / 16) * math.pi / 180
        center = rect.center()
        radius = rect.width() // 2 - 20
        
        needle_x = center.x() + radius * 0.8 * math.cos(angle_rad)
        needle_y = center.y() - radius * 0.8 * math.sin(angle_rad)
        
        painter.setPen(QPen(QColor(50, 50, 50), 3))
        painter.drawLine(center.x(), center.y(), int(needle_x), int(needle_y))
        
        painter.setBrush(QBrush(QColor(50, 50, 50)))
        painter.drawEllipse(center, 8, 8)
        
        painter.setPen(QColor(50, 50, 50))
        painter.setFont(QFont("Arial", 20, QFont.Bold))
        painter.drawText(rect, Qt.AlignCenter, f"{int(progress)}%")
        
        painter.end()
        self.progress_gauge.setPixmap(pixmap)
