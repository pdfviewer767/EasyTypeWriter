# ui/speed_test_runner.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QPlainTextEdit, QMessageBox
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor, QTextCharFormat, QColor
import time
from utils.tr import tr
from utils.resource import resource_path

class SpeedTestRunner(QWidget):
    test_finished = pyqtSignal(float, float, int)  # wpm, accuracy, duration
    back_requested = pyqtSignal()  # إشارة جديدة للعودة إلى واجهة الاختبارات

    def update_texts(self):
        self.timer_label.setText(tr("speed_test_timer"))
        self.finish_btn.setText(tr("finish_test"))
        # أضف تحديث بقية العناصر حسب الحاجة
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # شاشة العرض
        self.timer_label = QLabel("00:00")
        self.timer_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.timer_label)
        
        # منطقة النص
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setFont(QFont("Arial", 16))
        self.text_display.setStyleSheet("""
            QTextEdit {
                font-size: 18px;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #f9f9f9;
            }
        """)
        self.layout.addWidget(self.text_display)
        
        # منطقة الإدخال
        self.input_box = QPlainTextEdit()
        self.input_box.setFixedHeight(100)
        self.input_box.setStyleSheet("""
            QPlainTextEdit {
                font-size: 18px;
                padding: 10px;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                background-color: white;
            }
        """)
        self.input_box.textChanged.connect(self.check_text)
        self.layout.addWidget(self.input_box)
        
        # مؤشرات الأداء
        self.stats_layout = QHBoxLayout()
        self.wpm_label = QLabel(tr("wpm_label") + ": 0")
        self.accuracy_label = QLabel(tr("accuracy_label") + ": 0%")
        self.stats_layout.addWidget(self.wpm_label)
        self.stats_layout.addStretch()
        self.stats_layout.addWidget(self.accuracy_label)
        self.layout.addLayout(self.stats_layout)
       
        # المؤقت
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.seconds_left = 0
        self.current_index = 0  # لتتبع الحرف الحالي
        self.start_time = 0  # وقت بدء الاختبار
        self.total_chars = 0  # إجمالي الأحرف المكتوبة
        self.correct_chars = 0  # الأحرف الصحيحة
        self.initial_duration = 0  # المدة الابتدائية للاختبار
        self.current_text = ""  # النص الحالي للاختبار
        
        # زر الإنهاء
        self.finish_btn = QPushButton(tr("finish_test"))
        self.finish_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 16px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        self.finish_btn.clicked.connect(self.finish_test)
        self.layout.addWidget(self.finish_btn)

    def set_text(self, text, duration):
        """تعيين نص الاختبار ومدة الاختبار"""
        self.text_display.setText(text)
        self.original_text = text
        self.current_text = text  # تخزين النص الحالي
        self.seconds_left = duration
        self.initial_duration = duration  # تخزين المدة الابتدائية
        self.update_timer_display()
        self.current_index = 0
        self.highlight_text()
        
        # إعادة تعيين الإحصائيات
        self.wpm_label.setText(tr("wpm_label") + ": 0")
        self.accuracy_label.setText(tr("accuracy_label") + ": 0%")

    def start_test(self):
        """بدء الاختبار"""
        self.timer.start(1000)
        self.input_box.setFocus()
        self.input_box.clear()
        self.input_box.setEnabled(True)
        
        # تسجيل وقت البدء
        self.start_time = time.time()
        
        # إعادة تعيين الإحصائيات
        self.total_chars = 0
        self.correct_chars = 0
        
        # إعداد المؤشر للبدء من البداية
        cursor = self.input_box.textCursor()
        cursor.setPosition(0)
        self.input_box.setTextCursor(cursor)

    def update_timer(self):
        """تحديث المؤقت"""
        if self.seconds_left > 0:
            self.seconds_left -= 1
            self.update_timer_display()
            
            # تحديث الإحصائيات
            self.update_stats()
            
            if self.seconds_left <= 0:
                self.finish_test()
            
    def update_timer_display(self):
        """تحديث عرض المؤقت"""
        minutes = self.seconds_left // 60
        seconds = self.seconds_left % 60
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")
        
    def highlight_text(self):
        """تظليل النص بناءً على الإدخال مع تتبع المؤشر"""
        # احصل على محتوى النص الأصلي
        original_text = self.original_text
        
        # احصل على النص الذي كتبه المستخدم
        typed_text = self.input_box.toPlainText()
        
        # إنشاء كائن لتنسيق النص
        cursor = self.text_display.textCursor()
        cursor.select(QTextCursor.Document)
        
        # التنسيق الأساسي للنص كله
        default_format = QTextCharFormat()
        default_format.setForeground(QColor("#333"))  # اللون الأساسي
        cursor.setCharFormat(default_format)
        
        # تنسيق الأحرف المكتوبة
        for i in range(len(typed_text)):
            if i < len(original_text):
                cursor.setPosition(i, QTextCursor.MoveAnchor)
                cursor.setPosition(i+1, QTextCursor.KeepAnchor)
                
                if typed_text[i] == original_text[i]:
                    # إذا كان الحرف صحيحًا، لون أخضر
                    correct_format = QTextCharFormat()
                    correct_format.setForeground(QColor("#4CAF50"))  # أخضر
                    cursor.setCharFormat(correct_format)
                else:
                    # إذا كان الحرف خاطئًا، لون أحمر
                    wrong_format = QTextCharFormat()
                    wrong_format.setForeground(QColor("#f44336"))  # أحمر
                    cursor.setCharFormat(wrong_format)
        
        # تظليل الحرف الحالي (الذي يجب كتابته) باللون الأصفر
        if self.current_index < len(original_text):
            cursor.setPosition(self.current_index, QTextCursor.MoveAnchor)
            cursor.setPosition(self.current_index+1, QTextCursor.KeepAnchor)
            current_char_format = QTextCharFormat()
            current_char_format.setBackground(QColor("#FFEB3B"))  # أصفر
            cursor.setCharFormat(current_char_format)
        
        # نقل المؤشر المرئي للحرف الحالي
        cursor.setPosition(self.current_index, QTextCursor.MoveAnchor)
        self.text_display.setTextCursor(cursor)
        self.text_display.ensureCursorVisible()

    def check_text(self):
        """التحقق من النص المدخل"""
        # احصل على النص المكتوب
        typed_text = self.input_box.toPlainText()
        
        # تحديث المؤشر للحرف الحالي (عدد الأحرف المكتوبة)
        self.current_index = len(typed_text)
        
        # قم بتحديث التظليل
        self.highlight_text()
        
    def update_stats(self):
        """تحديث إحصائيات الأداء"""
        if self.start_time == 0:
            return
            
        # احسب الوقت المنقضي
        elapsed_time = time.time() - self.start_time
        minutes = elapsed_time / 60.0
        
        # احصل على النص المكتوب
        typed_text = self.input_box.toPlainText()
        
        # حساب الأحرف الصحيحة
        self.total_chars = len(typed_text)
        self.correct_chars = 0
        
        for i in range(min(len(typed_text), len(self.original_text))):
            if typed_text[i] == self.original_text[i]:
                self.correct_chars += 1
        
        # حساب كلمات في الدقيقة (WPM)
        if minutes > 0:
            wpm = (self.correct_chars / 5) / minutes
        else:
            wpm = 0
            
        # حساب الدقة
        if self.total_chars > 0:
            accuracy = (self.correct_chars / self.total_chars) * 100
        else:
            accuracy = 0
            
        # تحديث العلامات
        self.wpm_label.setText(f"{tr('wpm_label')}: {wpm:.1f}")
        self.accuracy_label.setText(f"{tr('accuracy_label')}: {accuracy:.1f}%")

    def finish_test(self):
        """إنهاء الاختبار وعرض النتائج"""
        self.timer.stop()
        
        # تحديث الإحصائيات النهائية
        self.update_stats()
        
        # إيقاف تفاعل منطقة الإدخال
        self.input_box.setEnabled(False)
        
        # حساب النتائج النهائية
        elapsed_time = time.time() - self.start_time
        minutes = elapsed_time / 60.0
        
        if minutes > 0:
            wpm = (self.correct_chars / 5) / minutes
        else:
            wpm = 0
            
        if self.total_chars > 0:
            accuracy = (self.correct_chars / self.total_chars) * 100
        else:
            accuracy = 0

        # إنشاء مربع الحوار المخصص
        dialog = QMessageBox(self)
        dialog.setWindowTitle(tr("test_results"))
        dialog.setIcon(QMessageBox.Information)
        
        # نص الرسالة مع النتائج
        message_text = tr("test_results_message").format(
            wpm=wpm,
            accuracy=accuracy,
            correct_chars=self.correct_chars,
            total_chars=self.total_chars
        )
        dialog.setText(message_text)
        
        # إضافة الأزرار
        retry_button = dialog.addButton(tr("retry_test"), QMessageBox.ActionRole)
        retry_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        
        back_button = dialog.addButton(tr("back_to_tests"), QMessageBox.RejectRole)
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0D47A1;
            }
        """)
        
        # تعيين الزر الافتراضي للتراجع (زر الهروب)
        dialog.setDefaultButton(back_button)
        
        # عرض مربع الحوار وانتظار رد المستخدم
        dialog.exec_()
        
        # معالجة اختيار المستخدم
        if dialog.clickedButton() == retry_button:
            # إعادة تعيين حالة الاختبار
            self.seconds_left = self.initial_duration
            self.update_timer_display()
            self.current_index = 0
            self.input_box.setEnabled(True)
            self.input_box.clear()
            self.highlight_text()
            
            # إعادة تعيين الإحصائيات
            self.wpm_label.setText(f"{tr('wpm_label')}: 0")
            self.accuracy_label.setText(f"{tr('accuracy_label')}: 0%")
            
            # إعادة بدء الاختبار
            self.start_test()
        else:
            # إصدار الإشارة للعودة إلى واجهة الاختبارات
            self.hide()
            if self.parent() and hasattr(self.parent(), 'speed_test_screen'):
                self.parent().speed_test_screen.show()
            elif hasattr(self.window(), 'speed_test_screen'):
                self.window().speed_test_screen.show()

    def set_focus(self):
        """تعيين التركيز على منطقة الإدخال"""
        self.input_box.setEnabled(True)
        self.input_box.setFocus()
        
        # وضع المؤشر في نهاية النص
        cursor = self.input_box.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.input_box.setTextCursor(cursor)