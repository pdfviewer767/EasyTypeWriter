# virtual_keyboard.py
import os
import sys
import json
import ctypes
import locale
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel, QApplication,
    QHBoxLayout, QFrame, QSizePolicy, QTextEdit
)
from PyQt5.QtGui import QFont, QKeyEvent, QPainter, QColor, QPalette
from PyQt5.QtCore import Qt, QEvent, QTimer, QSize
from utils.resource import user_data_path

# استخدام resource_path لمسارات الملفات بعد التحزيم
POSITIONS_FILE = user_data_path('data/finger_positions.json')

class KeyboardLanguageDetector:
    """فئة لاكتشاف لغة لوحة المفاتيح الحالية للنظام"""
    @staticmethod
    def detect():
        """اكتشف لغة النظام الحالية"""
        try:
            user32 = ctypes.WinDLL('user32', use_last_error=True)
            hwnd = user32.GetForegroundWindow()
            thread_id = user32.GetWindowThreadProcessId(hwnd, 0)
            klid = user32.GetKeyboardLayout(thread_id)
            lid = klid & (2**16 - 1)
            lang = locale.windows_locale.get(lid, '')
            return 'ar' if lang.startswith('ar') else 'en'
        except Exception:
            return 'en'

class FingerPositionManager:
    """مدير لإعدادات مواقع الأصابع"""
    def __init__(self, hand):
        self.hand = hand
        self.finger_positions = self.default_positions()
        self.base_position = [0.5, 0.85]
        self.load_positions()

    def load_positions(self):
        """تحميل الإعدادات من ملف JSON"""
        if os.path.exists(POSITIONS_FILE):
            try:
                with open(POSITIONS_FILE, 'r', encoding='utf-8') as f:
                    all_pos = json.load(f)
                    hand_data = all_pos.get(self.hand, {})
                    self.finger_positions = hand_data.get('fingers', self.default_positions())
                    self.base_position = hand_data.get('base', [0.5, 0.85])
            except (json.JSONDecodeError, IOError):
                # استعادة الإعدادات الافتراضية عند الخطأ
                self.finger_positions = self.default_positions()
                self.base_position = [0.5, 0.85]
        else:
            # إذا لم يوجد الملف، استخدم الإعدادات الافتراضية
            self.finger_positions = self.default_positions()
            self.base_position = [0.5, 0.85]

    def save_positions(self):
        """حفظ الإعدادات إلى ملف JSON"""
        # إنشاء مجلد data إذا لم يكن موجوداً
        data_dir = os.path.dirname(POSITIONS_FILE)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        all_pos = {}
        if os.path.exists(POSITIONS_FILE):
            try:
                with open(POSITIONS_FILE, 'r', encoding='utf-8') as f:
                    all_pos = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        all_pos[self.hand] = {
            'fingers': self.finger_positions,
            'base': self.base_position
        }
        
        try:
            with open(POSITIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_pos, f, indent=2, ensure_ascii=False)
        except IOError:
            pass

    def default_positions(self):
        """المواقع الافتراضية للأصابع"""
        if self.hand == 'left':
            return {
                "thumb": [0.3, 0.9, 0],
                "index": [0.45, 0.35, 0],
                "middle": [0.35, 0.25, 0],
                "ring": [0.2, 0.3, 0],
                "pinky": [0.05, 0.4, 0],
            }
        return {
            "thumb": [0.7, 0.9, 0],
            "index": [0.55, 0.35, 0],
            "middle": [0.65, 0.25, 0],
            "ring": [0.8, 0.3, 0],
            "pinky": [0.95, 0.4, 0],
        }

class FingerCanvas(QFrame):
    """لوحة لعرض مواقع الأصابع وتفاعلاتها"""
    def __init__(self, hand, parent=None):
        super().__init__(parent)
        self.position_manager = FingerPositionManager(hand)
        self.active_fingers = set()
        self.setMinimumSize(150, 200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("background-color: transparent;")

    def paintEvent(self, event):
        """رسم الأصابع والقاعدة"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # ألوان ثابتة
        base_color = QColor(220, 220, 220)
        active_color = QColor("#16a34a")
        finger_width = max(15, int(w * 0.05))
        finger_height = max(30, int(h * 0.2))

        # رسم قاعدة اليد
        base_width = max(40, int(w * 0.3))
        base_height = max(20, int(h * 0.2))
        base_x = int(w * self.position_manager.base_position[0] - base_width / 2)
        base_y = int(h * self.position_manager.base_position[1])
        painter.setBrush(base_color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(base_x, base_y, base_width, base_height)

        # رسم الأصابع
        for finger, values in self.position_manager.finger_positions.items():
            x, y = int(w * values[0]), int(h * values[1])
            angle = values[2] if len(values) > 2 else 0

            painter.save()
            painter.translate(x, y)
            painter.rotate(angle)
            rect_x = -finger_width // 2
            rect_y = -finger_height
            
            # تحديد لون الإصبع (نشط أو غير نشط)
            brush_color = active_color if finger in self.active_fingers else base_color
            painter.setBrush(brush_color)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(rect_x, rect_y, finger_width, finger_height, 10, 10)
            painter.restore()

    def set_active_finger(self, finger_name):
        """تعيين الإصبع النشط"""
        self.active_fingers = {finger_name}
        self.update()

    def clear_active(self):
        """مسح جميع الأصابع النشطة"""
        self.active_fingers.clear()
        self.update()

class VirtualKeyboardScreen(QWidget):
    """شاشة لوحة المفاتيح الافتراضية الكاملة"""
    KEYBOARD_LAYOUTS = {
        "ar": {
            "rows": [
                ["Esc", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"],
                ["ذ", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "="],
                ["Tab", "ض", "ص", "ث", "ق", "ف", "غ", "ع", "ه", "خ", "ح", "ج", "د"],
                ["Caps", "ش", "س", "ي", "ب", "ل", "ا", "ت", "ن", "م", "ك", "ط", "Enter"],
                ["Shift", "ئ", "ء", "ؤ", "ر", "لا", "ى", "ة", "و", "ز", "ظ", "Shift", "↑"],
                ["Ctrl", "Alt", "فراغ", "Alt", "Ctrl", "←", "↓", "→"],
            ],
            "special_keys": {
                "فراغ": "مسافة", 
                "Tab": "Tab",
                "Caps": "Caps",
                "Shift": "Shift",
                "Ctrl": "Ctrl",
                "Alt": "Alt",
                "Enter": "Enter",
                "Esc": "Esc"
            },
            "home_keys": ["ت", "ب"]
        },
        "en": {
            "rows": [
                ["ESC", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"],
                ["", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "BACKSPACE"],
                ["TAB", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]", "\\"],
                ["CAPS", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", "ENTER"],
                ["SHIFT", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "SHIFT", "↑"],
                ["CTRL", "ALT", "SPACE", "ALT", "CTRL", "←", "↓", "→"]
            ],
            "special_keys": {
                "SPACE": "Space",
                "TAB": "Tab",
                "CAPS": "Caps",
                "SHIFT": "Shift",
                "CTRL": "Ctrl",
                "ALT": "Alt",
                "ENTER": "Enter",
                "ESC": "Esc"
            },
            "home_keys": ["F", "J"]
        }
    }
    
    FINGER_MAPPING = {
        "ar": {
            "left": {
                "ض": "pinky", "ئ": "pinky", "ش": "pinky", "tab": "pinky", "Caps": "pinky", 
                "Shift": "pinky", "إزاحة": "pinky", "ذ": "pinky", "ص": "ring", "ء": "ring", 
                "س": "ring", "ث": "middle", "ؤ": "middle", "ي": "middle", "ق": "index", 
                "ف": "index", "ب": "index", "ل": "index", "ر": "index", "فراغ": "thumb"
            },
            "right": {
                "غ": "index", "ع": "index", "ت": "index", "ا": "index", "ى": "index", 
                "ة": "index", "لا": "index", "ه": "middle", "و": "middle", "ن": "middle", 
                "خ": "ring", "ز": "ring", "م": "ring", "ح": "pinky", "ج": "pinky", 
                "د": "pinky", "ك": "pinky", "ط": "pinky", "ظ": "pinky", "Enter": "pinky", 
                "إرجاع": "pinky", "؟": "pinky", "\\": "pinky", "/": "pinky", "فراغ": "thumb"
            }
        },
        "en": {
            "left": {
                "": "pinky", "1": "pinky", "q": "pinky", "a": "pinky", "z": "pinky", 
                "tab": "pinky", "caps": "pinky", "shift": "pinky", "esc": "pinky", 
                "2": "ring", "w": "ring", "s": "ring", "x": "ring", "3": "middle", 
                "e": "middle", "d": "middle", "c": "middle", "4": "index", "5": "index", 
                "r": "index", "t": "index", "f": "index", "g": "index", "v": "index", 
                "b": "index", "space": "thumb"
            },
            "right": {
                "6": "index", "7": "index", "y": "index", "u": "index", "h": "index", 
                "j": "index", "n": "index", "m": "index", "8": "middle", "i": "middle", 
                "k": "middle", ",": "middle", "9": "ring", "o": "ring", "l": "ring", 
                ".": "ring", "0": "pinky", "-": "pinky", "=": "pinky", "p": "pinky", 
                "[": "pinky", "]": "pinky", ";": "pinky", "'": "pinky", "\\": "pinky", 
                "/": "pinky", "enter": "pinky", "shift": "pinky", "backspace": "pinky", 
                "space": "thumb"
            }
        }
    }

    def __init__(self, settings=None, input_box=None):
        super().__init__()
        self.settings = settings
        self.input_box = input_box
        self.setFocusPolicy(Qt.StrongFocus)
        self.active_keys = set()
        self.language = KeyboardLanguageDetector.detect()
        self.last_language = self.language
        self.base_font_size = 16  # حجم خط أساسي أكبر
        self.setMinimumSize(800, 400)  # حجم أدنى مناسب للوحة المفاتيح
        self.init_ui()
        QApplication.instance().installEventFilter(self)

    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # لوحات الأصابع
        self.left_canvas = FingerCanvas('left')
        self.right_canvas = FingerCanvas('right')
        main_layout.addWidget(self.left_canvas, 1)

        # لوحة المفاتيح المركزية
        center_layout = QVBoxLayout()
        self.keyboard_grid = QGridLayout()
        self.keyboard_grid.setSpacing(5)  # تقليل التباعد بين الأزرار
        self.keys = {}
        self.build_keyboard()
        
        center_layout.addLayout(self.keyboard_grid)
        main_layout.addLayout(center_layout, 3)
        main_layout.addWidget(self.right_canvas, 1)

        self.setLayout(main_layout)
        
        # تحسين الوضوح للألوان
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#f0f0f0"))
        self.setPalette(palette)

    def build_keyboard(self):
        """بناء لوحة المفاتيح بناءً على اللغة الحالية"""
        # تنظيف لوحة المفاتيح الحالية
        for i in reversed(range(self.keyboard_grid.count())):
            if widget := self.keyboard_grid.itemAt(i).widget():
                widget.deleteLater()
        self.keys.clear()

        layout = self.KEYBOARD_LAYOUTS[self.language]
        rows = layout["rows"]
        special_keys = layout["special_keys"]
        home_keys = layout["home_keys"]

        for row_idx, row in enumerate(rows):
            col = 0
            for key in row:
                display_key = special_keys.get(key, key)
                btn = self.create_key_button(display_key, key, home_keys)
                self.keys[key] = btn
                
                # إضافة اختصارات للأحرف الصغيرة والكبيرة
                if key.isalpha():
                    self.keys[key.lower()] = btn
                    self.keys[key.upper()] = btn

                # تحديد حجم زر المسافة
                if key in ["فراغ", "SPACE"]:
                    # تقليل عرض زر المسافة ليتناسب مع التخطيط
                    self.keyboard_grid.addWidget(btn, row_idx, col, 1, 5)
                    col += 5
                else:
                    self.keyboard_grid.addWidget(btn, row_idx, col)
                    col += 1

    def create_key_button(self, display_text, key_name, home_keys):
        """إنشاء زر مفتاح مع تنسيق احترافي كما في التطبيقات الحديثة ويدعم الشاشات الصغيرة"""
        btn = QPushButton(display_text)
        btn.setEnabled(False)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # سيتم ضبط الخط لاحقاً في resizeEvent
        font_family = "Cairo, Segoe UI, Tajawal, Arial"
        btn.setFont(QFont(font_family, self.base_font_size, QFont.Bold))

        direction_keys = {"←", "→", "↑", "↓"}
        function_keys = {f"F{i}" for i in range(1, 13)}

        if key_name in direction_keys:
            style = f"""
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #60d7f9, stop:1 #38bdf8);
                color: #222;
                border: 2px solid #0ea5e9;
                border-radius: 10px;
                font-weight: bold;
                font-family: {font_family};
                padding: 10px 0;
                border-bottom: 3px solid #b0bec5;
                text-align: center;
            """
        elif key_name in function_keys:
            style = f"""
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #60a5fa, stop:1 #3b82f6);
                color: white;
                border: 2px solid #2563eb;
                border-radius: 10px;
                font-weight: bold;
                font-family: {font_family};
                padding: 10px 0;
                border-bottom: 3px solid #b0bec5;
                text-align: center;
            """
        elif key_name in home_keys or (self.language == "en" and key_name.upper() in home_keys):
            style = f"""
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fbbf24, stop:1 #f59e0b);
                color: white;
                border: 2px solid #d97706;
                border-radius: 10px;
                font-weight: bold;
                font-family: {font_family};
                padding: 10px 0;
                border-bottom: 3px solid #b0bec5;
                text-align: center;
            """
        else:
            style = f"""
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f8fafc, stop:1 #e5e7eb);
                color: #222;
                border: 2px solid #d1d5db;
                border-radius: 10px;
                font-weight: bold;
                font-family: {font_family};
                padding: 10px 0;
                border-bottom: 3px solid #b0bec5;
                text-align: center;
            """

        btn.setStyleSheet(style)
        btn.setMinimumSize(48, 48)  # أكبر قليلاً افتراضياً
        return btn

    def eventFilter(self, obj, event):
        """تصفية الأحداث لمعالجة ضغطات المفاتيح فقط إذا كان input_box هو النشط"""
        try:
            if self.input_box and self.input_box.hasFocus():
                if event.type() == QEvent.KeyPress:
                    return self.handle_key_event(event, is_press=True)
                elif event.type() == QEvent.KeyRelease:
                    return self.handle_key_event(event, is_press=False)
        except RuntimeError:
            # العنصر محذوف، تجاهل الكود
            pass
        return super().eventFilter(obj, event)

    def handle_key_event(self, event, is_press):
        """معالجة أحداث المفاتيح (ضغط أو إفلات)"""
        # تحديث لغة النظام أولاً
        self.update_language_from_system()
        
        # تمرير الحدث إلى صندوق النص إذا كان موجوداً
        if self.input_box:
            if is_press:
                self.input_box.keyPressEvent(event)
            else:
                self.input_box.keyReleaseEvent(event)
        
        # معالجة الحدث في لوحة المفاتيح الافتراضية
        if is_press:
            self.handle_key_press(event)
        else:
            self.handle_key_release(event)
            
        return True

    def update_language_from_system(self):
        """تحديث لغة لوحة المفاتيح بناءً على لغة النظام"""
        current_language = KeyboardLanguageDetector.detect()
        if current_language != self.language:
            self.language = current_language
            self.build_keyboard()

    def handle_key_press(self, event):
        """معالجة ضغط المفتاح"""
        key_name = self.get_key_name(event)
        if not key_name:
            return
            
        self.highlight_key(key_name)
        self.highlight_finger(key_name)
        
        # معالجة المفاتيح المركبة (Shift + حرف)
        if event.modifiers() & Qt.ShiftModifier and event.text():
            shift_key_name = f"Shift+{event.text()}"
            if shift_key_name in self.keys:
                self.highlight_key(shift_key_name)

    def handle_key_release(self, event):
        """معالجة إفلات المفتاح"""
        key_name = self.get_key_name(event)
        if key_name:
            self.restore_key_style(key_name)
            self.active_keys.discard(key_name)
            
        # معالجة المفاتيح المركبة
        if event.text() and (event.modifiers() & Qt.ShiftModifier):
            shift_key_name = f"Shift+{event.text()}"
            if shift_key_name in self.keys:
                self.restore_key_style(shift_key_name)
            
        # إزالة تمييز الأصابع
        self.left_canvas.clear_active()
        self.right_canvas.clear_active()

    def get_key_name(self, event):
        """الحصول على اسم المفتاح من الحدث"""
        key_code = event.key()
        key_text = event.text().strip()
        
        # تحويل الأحرف الخاصة العربية
        special_chars = {
            '؛': ';', '،': ',', '؟': '?', '÷': '/', '×': '*',
            'ِ': 'َ', 'ُ': 'ً', 'ٌ': 'ٌ', 'ٍ': 'ٍ', 'ّ': 'ّ'
        }
        key_text = special_chars.get(key_text, key_text)
        
        # مفتاح المسافة
        if key_code == Qt.Key_Space:
            return "فراغ" if self.language == "ar" else "SPACE"

        # مفاتيح خاصة
        special_keys = {
            Qt.Key_Escape: "ESC",
            Qt.Key_Tab: "TAB",
            Qt.Key_Backspace: "BACKSPACE",
            Qt.Key_Return: "ENTER",
            Qt.Key_Enter: "ENTER",
            Qt.Key_Shift: "SHIFT",
            Qt.Key_Control: "CTRL",
            Qt.Key_Alt: "ALT",
            Qt.Key_CapsLock: "CAPS",
            Qt.Key_Left: "←",
            Qt.Key_Right: "→",
            Qt.Key_Up: "↑",
            Qt.Key_Down: "↓"
        }
        
        # إرجاع اسم المفتاح المناسب
        if key_code in special_keys:
            return special_keys[key_code]
        return key_text if key_text else None

    def highlight_key(self, key_name):
        """تمييز المفتاح في لوحة المفاتيح"""
        if key_name in self.keys:
            btn = self.keys[key_name]
            btn.setStyleSheet("""
                background-color: #16a34a; 
                color: white; 
                border: 2px solid #15803d;
                border-radius: 8px;
                font-weight: bold;
                border-bottom: 3px solid #b0bec5;
            """)
            self.active_keys.add(key_name)

    def restore_key_style(self, key_name):
        """استعادة النمط الأصلي للمفتاح"""
        if key_name in self.keys:
            btn = self.keys[key_name]
            btn.setStyleSheet(self.get_key_style(key_name))

    def get_key_style(self, key_name):
        """الحصول على النمط المناسب للمفتاح"""
        direction_keys = {"←", "→", "↑", "↓"}
        function_keys = {f"F{i}" for i in range(1, 13)}
        home_keys = self.KEYBOARD_LAYOUTS[self.language]["home_keys"]
        
        if key_name in direction_keys:
            return """
                background-color: #38bdf8; 
                color: #222; 
                border: 2px solid #0ea5e9; 
                border-radius: 8px;
                font-weight: bold;
            border-bottom: 3px solid #b0bec5;
            """
        elif key_name in function_keys:
            return """
                background-color: #3b82f6; 
                color: white; 
                border: 2px solid #2563eb; 
                border-radius: 8px;
                font-weight: bold;
            border-bottom: 3px solid #b0bec5;
            """
        elif key_name in home_keys or (self.language == "en" and key_name.upper() in home_keys):
            return """
                background-color: #f59e0b; 
                color: white; 
                border: 2px solid #d97706; 
                border-radius: 8px;
                font-weight: bold;
            border-bottom: 3px solid #b0bec5;
            """
        return """
            background-color: #ffffff; 
            color: #222; 
            border: 2px solid #d1d5db; 
            border-radius: 8px;
            font-weight: bold;
            border-bottom: 3px solid #b0bec5;
        """

    def highlight_finger(self, key):
        """تمييز الإصبع المناسب على لوحة الأصابع"""
        # تجاهل أسماء المفاتيح المركبة
        if key.startswith("Shift+"):
            key = key.split("+")[1]
            
        key = key.lower().strip()
        special_keys = {" ": "space", "\t": "tab", "\n": "enter", "\r": "enter"}
        key = special_keys.get(key, key)
        
        # تحويل الأحرف الخاصة العربية إلى أحرف أساسية
        arabic_map = {
            'َ': 'ا', 'ً': 'ا', 'ُ': 'و', 'ٌ': 'و',
            'ِ': 'ي', 'ٍ': 'ي', 'ّ': ' '
        }
        key = arabic_map.get(key, key)

        # تحديد الإصبع النشط
        mapping = self.FINGER_MAPPING.get(self.language, {})
        if key in mapping.get("left", {}):
            self.left_canvas.set_active_finger(mapping["left"][key])
        elif key in mapping.get("right", {}):
            self.right_canvas.set_active_finger(mapping["right"][key])

    def resizeEvent(self, event):
        """تعديل حجم الخط والأزرار ديناميكياً حسب حجم النافذة"""
        super().resizeEvent(event)
        w = self.width()
        h = self.height()
        
        # تحسين حساب حجم الخط ديناميكياً
        base_size = min(w, h)
        font_size = max(10, base_size // 50)
        min_size = max(30, base_size // 25)
        
        font_family = "Cairo, Segoe UI, Tajawal, Arial"
        for btn in self.keys.values():
            btn.setFont(QFont(font_family, font_size, QFont.Bold))
            btn.setMinimumSize(min_size, min_size)
        self.left_canvas.update()
        self.right_canvas.update()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # إنشاء نافذة تجريبية
    window = VirtualKeyboardScreen()
    window.setWindowTitle("لوحة المفاتيح الافتراضية - محسنة للوضوح")
    window.setGeometry(100, 100, 1000, 500)
    
    # إضافة صندوق إدخال نص تجريبي
    input_box = QTextEdit()
    input_box.setPlaceholderText("اضغط هنا لبدء الكتابة...")
    input_box.setFont(QFont("Arial", 14))
    
    main_layout = QVBoxLayout()
    main_layout.addWidget(input_box)
    main_layout.addWidget(window)
    
    container = QWidget()
    container.setLayout(main_layout)
    container.show()
    
    sys.exit(app.exec_())