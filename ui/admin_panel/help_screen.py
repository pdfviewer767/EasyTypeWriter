# help_screen.py
# شاشة المساعدة والدعم الفني في التطبيق
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QListWidget, QListWidgetItem, QFormLayout, QLineEdit, QComboBox, QTextEdit, QPushButton, QFileDialog
from PyQt5.QtCore import Qt
from utils.tr import tr
from utils.translation_manager import TranslationManager
from utils.resource import resource_path

class HelpScreen(QWidget):
    def __init__(self, translation_manager=None):
        super().__init__()
        self.setMinimumSize(400, 300)
        self.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Expanding)
        if translation_manager is not None:
            self.translator = translation_manager
        else:
            from utils.tr import set_translation_manager
            from PyQt5.QtWidgets import QApplication
            from core.settings_manager import SettingsManager
            app = QApplication.instance()
            settings_manager = SettingsManager()
            self.translator = TranslationManager(app, settings_manager)
            set_translation_manager(self.translator)
        self.lang = self.translator.get_language() if hasattr(self.translator, "get_language") else "ar"
        self.is_rtl = self.lang == "ar"
        self.setLayoutDirection(Qt.RightToLeft if self.is_rtl else Qt.LeftToRight)

        main_layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # 1. دليل الاستخدام
        guide_tab = QWidget()
        guide_layout = QVBoxLayout(guide_tab)
        guide_layout.addWidget(QLabel(tr("guide_title", "🧭 دليل الاستخدام")))
        self.guide_user_combo = QComboBox()
        self.guide_user_combo.addItems([
            tr("student", "طالب"),
            tr("teacher", "معلم"),
            tr("admin", "مدير")
        ])
        guide_layout.addWidget(self.guide_user_combo)
        self.guide_text = QLabel()
        guide_layout.addWidget(self.guide_text)

        def update_guide():
            t = self.guide_user_combo.currentText()
            if t == tr("student", "طالب"):
                self.guide_text.setText(tr("student_guide", "- كيف يبدأ التمرين\n- كيف يتابع تقدمه\n[صورة/رابط فيديو]"))
            elif t == tr("teacher", "معلم"):
                self.guide_text.setText(tr("teacher_guide", "- كيف يضيف درسًا\n- كيفية متابعة الطلاب\n[صورة/رابط فيديو]"))
            else:
                self.guide_text.setText(tr("admin_guide", "- كيفية إدارة المستخدمين والصلاحيات\n[صورة/رابط فيديو]"))

        self.guide_user_combo.currentIndexChanged.connect(update_guide)
        update_guide()
        tabs.addTab(guide_tab, tr("tab_guide", "🧭 دليل الاستخدام"))

        # 2. الأسئلة الشائعة
        faq_tab = QWidget()
        faq_layout = QVBoxLayout(faq_tab)
        faq_layout.addWidget(QLabel(tr("faq_title", "💬 الأسئلة الشائعة")))
        faq_list = QListWidget()
        faqs = [
            (tr("faq_reset_password_q", "كيف أسترجع كلمة المرور؟"),
             tr("faq_reset_password_a", "اذهب إلى شاشة تسجيل الدخول، واضغط \"نسيت كلمة المرور\"")),
            (tr("faq_no_start_button_q", "لماذا لا يظهر زر بدء التمرين؟"),
             tr("faq_no_start_button_a", "تأكد من أنك اخترت درسًا أولًا")),
            (tr("faq_speed_calc_q", "كيف يتم احتساب سرعة الكتابة؟"),
             tr("faq_speed_calc_a", "عدد الكلمات الصحيحة في الدقيقة"))
        ]
        for q, a in faqs:
            item = QListWidgetItem(f"❓ {q}\n📝 {a}")
            faq_list.addItem(item)
        faq_layout.addWidget(faq_list)
        tabs.addTab(faq_tab, tr("tab_faq", "💬 الأسئلة الشائعة"))

        # 3. اتصل بنا
        contact_tab = QWidget()
        contact_layout = QFormLayout(contact_tab)
        contact_layout.addRow(QLabel(tr("contact_title", "📞 اتصل بنا")))
        self.contact_name = QLineEdit()
        contact_layout.addRow(tr("name", "الاسم:"), self.contact_name)
        self.contact_email = QLineEdit()
        contact_layout.addRow(tr("email", "البريد الإلكتروني:"), self.contact_email)
        self.contact_type = QComboBox()
        self.contact_type.addItems([
            tr("technical_issue", "مشكلة تقنية"),
            tr("inquiry", "استفسار"),
            tr("suggestion", "اقتراح")
        ])
        contact_layout.addRow(tr("issue_type", "نوع المشكلة:"), self.contact_type)
        self.contact_desc = QTextEdit()
        contact_layout.addRow(tr("issue_desc", "وصف المشكلة:"), self.contact_desc)
        send_btn = QPushButton(tr("send", "إرسال"))
        contact_layout.addRow(send_btn)
        tabs.addTab(contact_tab, tr("tab_contact", "📞 اتصل بنا"))

        # 4. فيديوهات تعليمية
        tut_tab = QWidget()
        tut_layout = QVBoxLayout(tut_tab)
        tut_layout.addWidget(QLabel(tr("tutorial_videos", "🎥 فيديوهات تعليمية")))
        tut_list = QListWidget()
        tutorials = [
            (tr("fast_typing", "مهارات الطباعة السريعة"), "https://www.youtube.com/watch?v=fast_typing"),
            (tr("hand_position", "وضعية اليد الصحيحة"), "https://www.youtube.com/watch?v=hand_position"),
            (tr("keyboard_usage", "كيفية استخدام لوحة المفاتيح"), "https://www.youtube.com/watch?v=keyboard_usage"),
            (tr("touch_typing", "التدريب على الطباعة باللمس"), "https://www.youtube.com/watch?v=touch_typing")
        ]
        for title, url in tutorials:
            item = QListWidgetItem(f"🎬 {title}\n🔗 {url}")
            tut_list.addItem(item)
        tut_layout.addWidget(tut_list)
        tabs.addTab(tut_tab, tr("tab_tutorials", "🎥 فيديوهات تعليمية"))

        # 5. الدعم الفني
        tech_tab = QWidget()
        tech_layout = QFormLayout(tech_tab)
        tech_layout.addRow(QLabel(tr("technical_support", "🛠️ الدعم الفني")))
        self.tech_device = QLineEdit()
        tech_layout.addRow(tr("device_type", "نوع الجهاز/النظام:"), self.tech_device)
        self.tech_desc = QTextEdit()
        tech_layout.addRow(tr("error_desc", "وصف الخطأ:"), self.tech_desc)
        self.tech_img_path = QLineEdit()
        self.tech_img_path.setReadOnly(True)
        img_btn = QPushButton(tr("attach_image", "إرفاق صورة"))

        def attach_img():
            path, _ = QFileDialog.getOpenFileName(self, tr("choose_image", "اختر صورة"), "", "Images (*.png *.jpg *.jpeg)")
            if path:
                self.tech_img_path.setText(path)

        img_btn.clicked.connect(attach_img)
        tech_layout.addRow(tr("error_image", "صورة الخطأ:"), self.tech_img_path)
        tech_layout.addRow("", img_btn)
        self.tech_date = QLineEdit()
        tech_layout.addRow(tr("error_date", "تاريخ الخطأ:"), self.tech_date)
        send_tech_btn = QPushButton(tr("send_report", "إرسال البلاغ"))
        tech_layout.addRow(send_tech_btn)
        tabs.addTab(tech_tab, tr("tab_support", "🛠️ الدعم الفني"))

        # 6. اقتراحات وتحسينات
        sugg_tab = QWidget()
        sugg_layout = QFormLayout(sugg_tab)
        sugg_layout.addRow(QLabel(tr("suggestions", "🔁 اقتراحات وتحسينات")))
        self.sugg_text = QTextEdit()
        sugg_layout.addRow(tr("suggestion_text", "الاقتراح:"), self.sugg_text)
        send_sugg_btn = QPushButton(tr("send_suggestion", "إرسال الاقتراح"))
        sugg_layout.addRow(send_sugg_btn)
        tabs.addTab(sugg_tab, tr("tab_suggestions", "🔁 اقتراحات وتحسينات"))

        main_layout.addWidget(tabs)
