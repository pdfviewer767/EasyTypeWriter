# lesson_runner.py
# شاشة تنفيذ الدروس في التطبيق
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QHBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QTextCursor, QColor, QTextCharFormat, QFont
import time
from utils.tr import tr

# استيراد لوحة المفاتيح الوهمية
from ui.virtual_keyboard import VirtualKeyboardScreen
from core.settings_manager import SettingsManager

class LessonRunner(QWidget):
    @property
    def current_lesson_title(self):
        """إرجاع عنوان الدرس الحالي (متوافق مع main_window)"""
        return self.lesson_title
    lesson_finished = pyqtSignal(str)  # إضافة عنوان الدرس في الإشارة

    def __init__(self):
        super().__init__()
        self.input_box = QTextEdit()
        self.start_time = None
        self.attempts = 0
        self.lesson_title = ""
        self.lesson_content = ""
        self.current_index = 0  # لتتبع الحرف الحالي
        self.settings = SettingsManager()
        self.keyboard = VirtualKeyboardScreen(self.settings, self.input_box)
        self.correct_chars = 0
        self.total_chars = 0

        layout = QVBoxLayout()

        # شريط العنوان
        header_layout = QHBoxLayout()
        self.title_label = QLabel(tr("lesson_title", "تمرين الطباعة"))
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(self.title_label)
        # أزرار التحكم
        self.end_btn = QPushButton(tr("end_lesson"))
        self.end_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        self.retry_btn = QPushButton(tr("retry_lesson"))
        self.retry_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        self.retry_btn.hide()
        self.back_btn = QPushButton(tr("back_to_main", "العودة للرئيسية"))
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #607d8b;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #455a64;
            }
        """)
        self.back_btn.hide()
        header_layout.addStretch()
        header_layout.addWidget(self.end_btn)
        header_layout.addWidget(self.retry_btn)
        header_layout.addWidget(self.back_btn)
        layout.addLayout(header_layout)

        # إحصائيات الأداء
        self.stats_layout = QHBoxLayout()
        self.wpm_label = QLabel(tr("wpm_label", "ك.د: 0"))
        self.accuracy_label = QLabel(tr("accuracy_label", "الدقة: 0%"))
        self.stats_layout.addWidget(self.wpm_label)
        self.stats_layout.addStretch()
        self.stats_layout.addWidget(self.accuracy_label)
        layout.addLayout(self.stats_layout)

        # عرض النص
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setFont(QFont("Arial", 16))
        self.text_display.setStyleSheet("""
            QTextEdit {
                font-size: 22px; 
                padding: 12px; 
                background: #f1f1f1; 
                color: #222;
                border-radius: 8px;
                margin: 10px 0;
            }
        """)
        layout.addWidget(self.text_display)

        # حقل الإدخال
        self.input_box.setStyleSheet("""
            QTextEdit {
                font-size: 18px;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.input_box)

        # لوحة المفاتيح تحت مربع النص مباشرة
        layout.addWidget(self.keyboard)

        # التغذية الراجعة
        self.feedback_label = QLabel("")
        self.feedback_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 16px;")
        layout.addWidget(self.feedback_label)

        self.setLayout(layout)

        # الاتصالات
        self.input_box.textChanged.connect(self.check_input)
        self.end_btn.clicked.connect(self.end_lesson)
        self.retry_btn.clicked.connect(self.retry_lesson)
        self.back_btn.clicked.connect(self.back_to_main.emit)

    # إشارة العودة للرئيسية
    back_to_main = pyqtSignal()

    def retry_lesson(self):
        """إعادة الدرس من البداية بنفس العنوان والمحتوى"""
        self.retry_btn.hide()
        self.back_btn.hide()
        self.start_lesson(self.lesson_title, self.lesson_content)

        self.setFocusPolicy(Qt.StrongFocus)
        self.apply_text_display_style()

    def set_titles(self, lesson_title, end_btn_text):
        self.title_label.setText(tr(lesson_title, lesson_title))
        self.end_btn.setText(tr(end_btn_text, end_btn_text))

    def update_texts(self):
        # تحديث النصوص الثابتة في الواجهة
        self.title_label.setText(tr("lesson_title"))
        self.end_btn.setText(tr("end_lesson"))
        self.retry_btn.setText(tr("retry_lesson"))
        self.back_btn.setText(tr("back_to_main"))
        self.wpm_label.setText(tr("wpm_label"))
        self.accuracy_label.setText(tr("accuracy_label"))

    def toggle_theme(self):
        try:
            current = self.settings.get("theme")
        except AttributeError:
            current = "الوضع النهاري"
        new_theme = "الوضع الليلي" if current == "الوضع النهاري" else "الوضع النهاري"
        try:
            self.settings.set("theme", new_theme)
        except AttributeError:
            pass
        from PyQt5.QtWidgets import QApplication
        self.settings.apply_theme(QApplication.instance())
        self.apply_text_display_style()

    def apply_text_display_style(self):
        # معالجة الخطأ في حالة عدم وجود طريقة get
        try:
            theme = self.settings.get("theme")
        except AttributeError:
            theme = "الوضع النهاري"  # قيمة افتراضية
            
        if theme == "الوضع الليلي":
            self.text_display.setStyleSheet("""
                QTextEdit {
                    font-size: 22px; 
                    padding: 12px; 
                    background: #334155; 
                    color: #e2e8f0;
                    border-radius: 8px;
                    margin: 10px 0;
                }
            """)
            self.input_box.setStyleSheet("""
                QTextEdit {
                    font-size: 18px;
                    padding: 12px;
                    background: #1e293b;
                    color: #f8fafc;
                    border: 2px solid #475569;
                    border-radius: 8px;
                }
            """)
        else:
            self.text_display.setStyleSheet("""
                QTextEdit {
                    font-size: 22px; 
                    padding: 12px; 
                    background: #f1f1f1; 
                    color: #222;
                    border-radius: 8px;
                    margin: 10px 0;
                }
            """)
            self.input_box.setStyleSheet("""
                QTextEdit {
                    font-size: 18px;
                    padding: 12px;
                    background: white;
                    color: #222;
                    border: 2px solid #ddd;
                    border-radius: 8px;
                }
            """)

    def start_lesson(self, title, content):
        self.lesson_title = title
        self.lesson_content = content
        self.title_label.setText(tr("lesson_title", title))
        self.text_display.setText(content)
        self.apply_text_display_style()
        self.input_box.setText("")
        self.feedback_label.setText("")
        self.attempts += 1
        self.start_time = time.time()
        self.keyboard.show()
        self.input_box.setFocus()
        self.current_index = 0
        self.correct_chars = 0
        self.total_chars = 0
        self.update_stats()
        self.highlight_text()
        self.update_texts()

    def set_lesson(self, title, content):
        self.start_lesson(title, content)

    def highlight_text(self):
        """تظليل النص بناءً على الإدخال مع تتبع المؤشر"""
        # احصل على محتوى النص الأصلي
        original_text = self.lesson_content
        
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
        if len(typed_text) < len(original_text):
            cursor.setPosition(len(typed_text), QTextCursor.MoveAnchor)
            cursor.setPosition(len(typed_text)+1, QTextCursor.KeepAnchor)
            current_char_format = QTextCharFormat()
            current_char_format.setBackground(QColor("#FFEB3B"))  # أصفر
            cursor.setCharFormat(current_char_format)
        
        # نقل المؤشر المرئي للحرف الحالي
        cursor.setPosition(len(typed_text), QTextCursor.MoveAnchor)
        self.text_display.setTextCursor(cursor)
        self.text_display.ensureCursorVisible()

    def update_stats(self):
        """تحديث إحصائيات الأداء"""
        if self.start_time is None:
            return
            
        # احسب الوقت المنقضي
        elapsed_time = time.time() - self.start_time
        minutes = elapsed_time / 60.0
        
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
        self.wpm_label.setText(f"ك.د: {wpm:.1f}")
        self.accuracy_label.setText(f"الدقة: {accuracy:.1f}%")

    def check_input(self):
        if not self.start_time:
            return

        # احصل على النص المكتوب
        typed_text = self.input_box.toPlainText()

        # تحديث المؤشر للحرف الحالي (عدد الأحرف المكتوبة)
        self.current_index = len(typed_text)

        # تحديث التظليل
        self.highlight_text()

        # تحديث الإحصائيات
        self.total_chars = len(typed_text)
        self.correct_chars = 0

        for i in range(min(len(typed_text), len(self.lesson_content))):
            if typed_text[i] == self.lesson_content[i]:
                self.correct_chars += 1
        self.update_stats()
        # إذا كان النص المكتوب يساوي النص الأصلي، نهاية الدرس
        if typed_text == self.lesson_content:
            # حساب الدقة
            accuracy = 0
            if self.total_chars > 0:
                accuracy = (self.correct_chars / self.total_chars) * 100
            time_spent = time.time() - self.start_time
            if accuracy < 90:
                QMessageBox.warning(
                    self,
                    "الدقة غير كافية",
                    f"يجب أن تكون الدقة 90% على الأقل لإكمال الدرس.\nدقتك الحالية: {accuracy:.1f}%"
                )
                self.retry_btn.show()
                self.back_btn.show()
                return
            self.feedback_label.setText(
                f"✅ تم بنجاح! الوقت: {round(time_spent, 2)} ثانية، المحاولة: {self.attempts}"
            )
            self.keyboard.hide()
            # عرض النتائج في رسالة
            QMessageBox.information(
                self, 
                "تهانينا!",
                f"لقد أكملت الدرس بنجاح!\n"
                f"الوقت المستغرق: {round(time_spent, 2)} ثانية\n"
                f"عدد المحاولات: {self.attempts}\n"
                f"سرعة الكتابة: {self.wpm_label.text()}\n"
                f"الدقة: {self.accuracy_label.text()}"
            )
            self.retry_btn.show()
            self.back_btn.show()
            self.end_lesson()

    def get_duration(self):
        if self.start_time is None:
            return 0
        return time.time() - self.start_time

    def get_avg_speed(self):
        duration_minutes = self.get_duration() / 60
        if duration_minutes <= 0:
            return 0
        return (self.correct_chars / 5) / duration_minutes

    def get_accuracy(self):
        if self.total_chars <= 0:
            return 0
        return (self.correct_chars / self.total_chars) * 100

    def get_error_details(self):
        errors = {}
        typed_text = self.input_box.toPlainText()
        for expected, actual in zip(self.lesson_content, typed_text):
            if expected != actual:
                errors[expected] = errors.get(expected, 0) + 1
        return errors

    def get_error_count(self):
        return sum(self.get_error_details().values())

    def end_lesson(self):
        if self.lesson_content and self.input_box.toPlainText() != self.lesson_content:
            QMessageBox.warning(
                self,
                tr("lesson_incomplete_title", "الدرس غير مكتمل"),
                tr("lesson_incomplete_message", "أكمل كتابة نص الدرس قبل إنهائه."),
            )
            self.retry_btn.show()
            self.back_btn.show()
            return

        accuracy = 0
        if self.total_chars > 0:
            accuracy = (self.correct_chars / self.total_chars) * 100
        if self.lesson_content and accuracy < 90:
            QMessageBox.warning(
                self,
                tr("accuracy_not_enough_title", "الدقة غير كافية"),
                tr("accuracy_not_enough_msg", f"يجب أن تكون الدقة 90% على الأقل لإكمال الدرس.\nدقتك الحالية: {accuracy:.1f}%")
            )
            self.retry_btn.show()
            self.back_btn.show()
            return
        # إرسال إشارة الإكمال مع عنوان الدرس
        self.lesson_finished.emit(self.lesson_title)

        # إعادة تعيين الحالة
        self.input_box.clear()
        self.feedback_label.setText("")
        self.attempts = 0
        self.start_time = None
        self.lesson_title = ""
        self.lesson_content = ""
        self.keyboard.hide()
        self.wpm_label.setText(tr("wpm_label", "ك.د: 0"))
        self.accuracy_label.setText(tr("accuracy_label", "الدقة: 0%"))
        self.retry_btn.hide()
        self.back_btn.hide()
        self.update_texts()

    def keyPressEvent(self, event):
        self.keyboard.keyPressEvent(event)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        self.keyboard.keyReleaseEvent(event)
        super().keyReleaseEvent(event)
        
    def set_focus(self):
        self.input_box.setFocus()
        cursor = self.input_box.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.input_box.setTextCursor(cursor)
