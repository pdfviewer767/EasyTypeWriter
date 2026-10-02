# header_bar.py

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from utils.tr import tr  # دالة الترجمة
from utils.resource import resource_path

class HeaderBar(QWidget):
    def __init__(self, tab_switch_callback, translation_manager, is_admin=False, on_admin_panel_open=None):
        super().__init__()
        self.tab_switch_callback = tab_switch_callback
        self.translation_manager = translation_manager
        self.tabs = {}
        self.is_admin = is_admin
        self.on_admin_panel_open = on_admin_panel_open

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 10, 15, 10)
        self.layout.setSpacing(10)

        self.lessons_btn = QPushButton()
        self.lessons_btn.clicked.connect(lambda: self.tab_switch_callback("lessons"))
        self.tabs["lessons"] = self.lessons_btn

        self.speed_test_btn = QPushButton()
        self.speed_test_btn.clicked.connect(lambda: self.tab_switch_callback("speed_test"))
        self.tabs["speed_test"] = self.speed_test_btn

        self.practice_btn = QPushButton()
        self.practice_btn.clicked.connect(lambda: self.tab_switch_callback("practice_texts"))
        self.tabs["practice_texts"] = self.practice_btn

        self.layout.addWidget(self.lessons_btn)
        self.layout.addWidget(self.speed_test_btn)
        self.layout.addWidget(self.practice_btn)

        if is_admin and on_admin_panel_open:
            self.admin_btn = QPushButton()
            self.admin_btn.setObjectName("adminPanelButton")
            self.admin_btn.clicked.connect(on_admin_panel_open)
            self.layout.addWidget(self.admin_btn)

        self.update_texts()

    def update_texts(self):
        self.lessons_btn.setText(tr("lessons", "الدروس"))
        self.speed_test_btn.setText(tr("speed_test", "اختبار السرعة"))
        self.practice_btn.setText(tr("practice_texts", "تمارين الكتابة"))
        if hasattr(self, 'admin_btn'):
            self.admin_btn.setText(tr("admin_panel", "لوحة تحكم الأدمن"))

    def highlight_tab(self, name):
        for tab_name, btn in self.tabs.items():
            btn.setProperty("active", "true" if tab_name == name else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def set_tab_enabled(self, tab_name, enabled):
        if tab_name in self.tabs:
            btn = self.tabs[tab_name]
            btn.setEnabled(enabled)
            btn.setProperty("enabled", "true" if enabled else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            if enabled:
                btn.setToolTip("")
            else:
                btn.setToolTip(tr("complete_previous_requirements", "يجب إكمال المتطلبات السابقة"))
