import json
import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt5.QtCore import Qt
from utils.tr import tr
from utils.resource import resource_path, user_data_path

class SpeedTestScreen(QWidget):
    def __init__(self, username):
        super().__init__()

        self.username = username  # اسم المستخدم لتحديد ملف التقدم
        self.lang = "ar"  # الافتراضي عربي
        self.messages = {}
        self.current_level = None

        # نتائج المستخدم لكل مستوى
        self.user_scores = {
            "Beginner": 0,
            "Intermediate": 0,
            "Advanced": 0
        }

        # تحميل بيانات المستخدم من ملف user_progress_XXX.json
        self.user_file = user_data_path(f"data/user_progress_{self.username}.json")
        self.load_user_scores()

        # اتجاه الواجهة
        self.apply_layout_direction()

        # تخطيط رئيسي
        self.layout = QVBoxLayout()

        # عنوان (رسالة ترحيب)
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e88e5;")
        self.layout.addWidget(self.title_label)

        # نص (التعليمات)
        self.message_text = QTextEdit()
        self.message_text.setReadOnly(True)
        self.message_text.setStyleSheet("font-size: 16px;")
        self.layout.addWidget(self.message_text)

        # الأزرار (للمستويات)
        self.five_min_btn = QPushButton()
        self.three_min_btn = QPushButton()
        self.one_min_btn = QPushButton()

        # شريط الأزرار
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.addStretch()
        for btn in [self.five_min_btn, self.three_min_btn, self.one_min_btn]:
            self.buttons_layout.addWidget(btn)
        self.buttons_layout.addStretch()
        self.layout.addLayout(self.buttons_layout)

        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)

        # تحميل الرسائل من messages.json
        self.load_messages()
        self.update_button_texts()

        # اعرض الرسالة الافتراضية (Advanced)
        self.show_message("Advanced")

        # ضبط حجم الأزرار ديناميكيًا
        self.update_buttons_size()
        self.resizeEvent = self.on_resize

        # تحديث حالة الأزرار حسب تقدم المستخدم
        self.update_buttons_state()

    # ---------- إعداد الاتجاه ----------
    def apply_layout_direction(self):
        if self.lang.lower().startswith("ar"):
            self.setLayoutDirection(Qt.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LeftToRight)

    # ---------- تحميل الرسائل ----------
    def load_messages(self):
        file_name = "data/messages.json"
        full_path = resource_path(file_name)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                self.messages = json.load(f)
        except Exception as e:
            self.messages = {"ar": {}, "en": {}}
            self.title_label.setText("⚠️ لم يتم العثور على ملف الرسائل")
            self.message_text.setText(str(e))

    # ---------- عرض الرسالة ----------
    def show_message(self, level: str):
        self.current_level = level
        lang_key = "ar" if self.lang.startswith("ar") else "en"
        msg = self.messages.get(lang_key, {})
        self.title_label.setText(msg.get("welcome", ""))
        self.message_text.setText(msg.get("instructions", ""))

    # ---------- تحديث نصوص الأزرار ----------
    def update_button_texts(self):
        self.five_min_btn.setText(tr("speed_test_five_min"))      # 5 دقائق
        self.three_min_btn.setText(tr("speed_test_three_min"))    # 3 دقائق
        self.one_min_btn.setText(tr("speed_test_one_min"))        # دقيقة واحدة
        # تلميحات
        self.five_min_btn.setToolTip("Beginner")
        self.three_min_btn.setToolTip("Intermediate")
        self.one_min_btn.setToolTip("Advanced")

    # ---------- تحديث حالة الأزرار حسب مستوى المستخدم ----------
    def update_buttons_state(self):
        self.five_min_btn.setEnabled(True)  # المبتدئ دائمًا مفعل
        self.three_min_btn.setEnabled(self.user_scores.get("Beginner", 0) >= 90)
        self.one_min_btn.setEnabled(self.user_scores.get("Intermediate", 0) >= 90)

    # ---------- التحكم في حجم الأزرار ----------
    def update_buttons_size(self):
        total_width = self.width() - 40
        button_width = max(120, total_width // 3)
        button_height = 50
        for btn in [self.one_min_btn, self.three_min_btn, self.five_min_btn]:
            btn.setFixedSize(button_width, button_height)

    def on_resize(self, event):
        self.update_buttons_size()

    # ---------- تغيير اللغة ----------
    def update_language(self, lang):
        self.lang = lang
        self.apply_layout_direction()
        self.load_messages()
        self.update_button_texts()
        self.show_message(self.current_level or "Advanced")

    # ---------- تحميل نتائج المستخدم ----------
    def load_user_scores(self):
        if not os.path.exists(self.user_file):
            # إنشاء الملف إذا لم يكن موجودًا
            self.save_user_scores()
        try:
            with open(self.user_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # جلب نتائج speed_test إذا وجدت
            speed_test_scores = data.get("speed_test_scores", {})
            self.user_scores.update(speed_test_scores)
        except Exception as e:
            print("Error loading user scores:", e)

    # ---------- حفظ نتائج المستخدم ----------
    def save_user_scores(self):
        data = {}
        if os.path.exists(self.user_file):
            try:
                with open(self.user_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except:
                data = {}

        # تحديث نتائج speed_test
        data["speed_test_scores"] = self.user_scores
        try:
            with open(self.user_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print("Error saving user scores:", e)

    # ---------- استدعاء عند انتهاء أي اختبار ----------
    def finish_test(self, level, score):
        """
        level: "Beginner" / "Intermediate" / "Advanced"
        score: نسبة اجتياز المستخدم (0-100)
        """
        self.user_scores[level] = score
        self.save_user_scores()
        self.update_buttons_state()
