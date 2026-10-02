import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, 
    QHBoxLayout, QMessageBox, QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from utils.tr import tr
from ui.virtual_keyboard import VirtualKeyboardScreen
from core.settings_manager import SettingsManager
from utils.resource import resource_path


class PracticeRunner(QWidget):
    # إشارات معدلة لتستقبل معاملات
    switch_to_practice_screen = pyqtSignal(dict)
    level_completed_signal = pyqtSignal(dict)
    next_text_requested = pyqtSignal()

    def __init__(self, text_data=None):
        super().__init__()
        self.text_data = text_data
        self.start_time = None
        self.timer_running = False
        self.elapsed_time = 0
        self.next_text_available = None
        
        # إعداد واجهة المستخدم
        self.init_ui()
        
        # إعداد المؤقت
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)  # تعيين التخطيط مباشرة للويدجت
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # شريط العنوان والإحصائيات
        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(10, 0, 10, 10)
        title_bar.setSpacing(15)
        
        # زر التحقق
        self.check_btn = QPushButton(tr("check"))
        self.check_btn.clicked.connect(self.check_results)
        self.check_btn.setObjectName("check_btn")
        self.check_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.check_btn.setMinimumSize(90, 50)
        
        # مؤشر الوقت
        self.time_label = QLabel("00:00 " + tr("time"))
        self.time_label.setObjectName("title_bar")
        self.time_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.time_label.setMinimumSize(90, 40)
        
        # دقة الكتابة
        self.accuracy_label = QLabel("0% " + tr("accuracy"))
        self.accuracy_label.setObjectName("title_bar")
        self.accuracy_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.accuracy_label.setMinimumSize(90, 40)

        # سرعة الكتابة (كلمات/دقيقة)
        self.speed_label = QLabel("0 " + tr("wpm"))
        self.speed_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.speed_label.setMinimumSize(90, 40)
        self.speed_label.setObjectName("title_bar")

        # عنوان النص
        if self.text_data:
            self.title_label = QLabel(self.text_data.get("title", tr("untitled_text")))
        else:
            self.title_label = QLabel(tr("untitled_text"))
        self.title_label.setObjectName("title_label")
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.title_label.setAlignment(Qt.AlignCenter)
        
        # إضافة العناصر إلى شريط العنوان
        title_bar.addWidget(self.check_btn)
        title_bar.addWidget(self.time_label)
        title_bar.addWidget(self.accuracy_label)
        title_bar.addWidget(self.speed_label)
        title_bar.addWidget(self.title_label)
        
        main_layout.addLayout(title_bar)
        
        # النص الأصلي
        self.original_text = QTextEdit()
        if self.text_data:
            self.original_text.setPlainText(self.text_data.get("content", tr("no_content")))
        else:
            self.original_text.setPlainText(tr("no_content"))
        
        self.original_text.setReadOnly(True)
        self.original_text.setObjectName("original_text")
        self.original_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.original_text.setMinimumHeight(100)
        main_layout.addWidget(self.original_text, 1)  # عامل التمدد 1
        
        # منطقة إدخال النص
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText(tr("start_typing_here"))
        self.input_text.setObjectName("input_text")
        self.input_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.input_text.setMinimumHeight(100)
        self.input_text.textChanged.connect(self.check_text)
        main_layout.addWidget(self.input_text, 1)  # عامل التمدد 1
        
        # تعيين التركيز على منطقة الكتابة
        self.input_text.setFocus()

        # لوحة المفاتيح الوهمية
        self.settings = SettingsManager()
        self.keyboard = VirtualKeyboardScreen(self.settings, self.input_text)
        self.keyboard.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.keyboard, 2)  # عامل تمدد أكبر للوحة المفاتيح
        
        # ضبط حجم الخط الأولي
        self.adjust_font_size()
    
    def adjust_font_size(self):
        """ضبط حجم الخط بناءً على حجم النافذة"""
        base_font_size = max(10, self.width() // 80)
        
        # تطبيق حجم الخط على العناصر
        font = QFont()
        font.setPointSize(base_font_size)
        
        # تطبيق حجم الخط على العناصر النصية
        for widget in [
            self.check_btn, self.time_label, 
            self.accuracy_label, self.speed_label,
            self.title_label
        ]:
            widget.setFont(font)
        
        # حجم خط أكبر قليلاً لمناطق النص
        text_font = QFont()
        text_font.setPointSize(base_font_size + 2)
        self.original_text.setFont(text_font)
        self.input_text.setFont(text_font)
    
    def resizeEvent(self, event):
        """تعديل حجم الخط ديناميكياً بناءً على حجم النافذة"""
        super().resizeEvent(event)
        self.adjust_font_size()
    
    def set_text_data(self, text_data):
        """تعيين بيانات نصية جديدة وإعادة تهيئة الواجهة"""
        self.text_data = text_data
        if self.text_data:
            self.title_label.setText(self.text_data.get("title", tr("untitled_text")))
            self.original_text.setPlainText(self.text_data.get("content", tr("no_content")))
        self.restart_practice()
        
    def start_timer(self):
        """بدء المؤقت عند البدء في الكتابة"""
        if not self.timer_running:
            self.start_time = time.time()
            self.timer.start(100)
            self.timer_running = True
    
    def update_timer(self):
        """تحديث المؤقت"""
        if self.start_time:
            self.elapsed_time = time.time() - self.start_time
            minutes = int(self.elapsed_time // 60)
            seconds = int(self.elapsed_time % 60)
            self.time_label.setText(f"{minutes:02d}:{seconds:02d} {tr('time')}")
    
    def check_text(self):
        """فحص النص أثناء الكتابة"""
        if not self.timer_running and self.input_text.toPlainText().strip():
            self.start_timer()
        
        if self.timer_running:
            self.calculate_accuracy()
    
    def calculate_accuracy(self):
        """حساب دقة الكتابة الحالية بناءً على الكلمات الصحيحة"""
        correct_words, total_words = self._get_word_counts()
        accuracy = (correct_words / total_words) * 100 if total_words else 0
        
        self.accuracy_label.setText(f"{accuracy:.1f}% {tr('accuracy')}")
        
        # حساب سرعة الكتابة (كلمات في الدقيقة)
        typed_words = self.input_text.toPlainText().split()
        words_typed = len(typed_words)
        minutes = self.elapsed_time / 60
        wpm = words_typed / minutes if minutes > 0 else 0
        
        self.speed_label.setText(f"{wpm:.1f} {tr('wpm')}")
    
    def check_results(self):
        """التحقق من النتائج النهائية"""
        session_data = self.get_session_data()
        
        if session_data["passed"]:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle(tr("success_title"))
            msg.setText(tr("success_message").format(
                accuracy=f"{session_data['accuracy']:.1f}",
                wpm=f"{session_data['wpm']:.1f}"
            ))
            
            has_next_text = self.has_next_text()
            next_btn = None
            if has_next_text:
                next_btn = msg.addButton(tr("next_exercise"), QMessageBox.AcceptRole)
            
            menu_btn = msg.addButton(tr("back_to_menu"), QMessageBox.RejectRole)
            
            msg.exec_()
            
            if has_next_text and msg.clickedButton() == next_btn:
                self.level_completed_signal.emit(session_data)
                self.next_text_requested.emit()
            else:
                self.level_completed_signal.emit(session_data)
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle(tr("try_again_title"))
            msg.setText(tr("try_again_message").format(accuracy=f"{session_data['accuracy']:.1f}"))
            
            retry_btn = msg.addButton(tr("retry"), QMessageBox.AcceptRole)
            menu_btn = msg.addButton(tr("back_to_menu"), QMessageBox.RejectRole)
            
            msg.exec_()
            
            if msg.clickedButton() == retry_btn:
                self.restart_practice()
            else:
                self.back_to_practice()

    def get_session_data(self):
        """الحصول على بيانات الجلسة الحالية"""
        correct_words, total_words = self._get_word_counts()
        accuracy = (correct_words / total_words) * 100 if total_words else 0
        
        # حساب سرعة الكتابة (كلمات في الدقيقة)
        typed_words = self.input_text.toPlainText().split()
        words_typed = len(typed_words)
        minutes = self.elapsed_time / 60
        wpm = words_typed / minutes if minutes > 0 else 0
        
        return {
            "accuracy": accuracy,
            "wpm": wpm,
            "duration": self.elapsed_time,
            "passed": accuracy >= 90,
            "correct_words": correct_words,
            "total_words": total_words
        }

    def _get_word_counts(self):
        original_words = self.original_text.toPlainText().split()
        typed_words = self.input_text.toPlainText().split()
        correct_words = sum(
            original == typed
            for original, typed in zip(original_words, typed_words)
        )
        return correct_words, max(len(original_words), len(typed_words))
    
    def restart_practice(self):
        """إعادة بدء التمرين"""
        self.input_text.clear()
        self.start_time = None
        self.timer_running = False
        self.elapsed_time = 0
        self.time_label.setText(f"00:00 {tr('time')}")
        self.accuracy_label.setText(f"0% {tr('accuracy')}")
        self.speed_label.setText(f"0 {tr('wpm')}")
        self.timer.stop()
        self.input_text.setFocus()
    
    def back_to_practice(self):
        """العودة إلى شاشة التدريب"""
        session_data = self.get_session_data()
        self.switch_to_practice_screen.emit(session_data)
    
    def set_focus(self):
        """تعيين التركيز على حقل الإدخال"""
        self.input_text.setFocus()
    
    def set_next_text_available_callback(self, callback):
        self.next_text_available = callback

    def has_next_text(self):
        """التحقق مما إذا كان هناك نص تالي في نفس المستوى"""
        return bool(self.next_text_available and self.next_text_available())