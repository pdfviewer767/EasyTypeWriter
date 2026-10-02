from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from utils.tr import tr


class HomeWidget(QWidget):
    def __init__(self, parent=None, is_admin=False):
        super().__init__(parent)
        self.is_admin = is_admin
        self.tab_buttons = []
        self.setup_ui()
        
    def setup_ui(self):
        home_layout = QVBoxLayout()
        home_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        home_layout.setContentsMargins(32, 48, 32, 48)
        home_layout.setSpacing(28)
        self.setLayout(home_layout)

        tab_names = [
            ("lessons", tr("lessons")),
            ("speed_test", tr("speed_test")),
            ("practice_texts", tr("practice_texts"))
        ]
        
        for tab_key, tab_label in tab_names:
            btn = QPushButton(tab_label)
            btn.setFixedHeight(60)
            btn.setMinimumWidth(260)
            btn.setMaximumWidth(340)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, name=tab_key: self.on_tab_clicked(name))
            home_layout.addWidget(btn, alignment=Qt.AlignHCenter)
            self.tab_buttons.append(btn)

        if self.is_admin:
            admin_btn = QPushButton(tr("admin_panel"))
            admin_btn.setObjectName("admin_btn")
            admin_btn.setFixedHeight(60)
            admin_btn.setMinimumWidth(260)
            admin_btn.setMaximumWidth(340)
            admin_btn.setCursor(Qt.PointingHandCursor)
            admin_btn.clicked.connect(lambda: self.on_tab_clicked("admin_panel"))
            home_layout.addWidget(admin_btn, alignment=Qt.AlignHCenter)
            self.tab_buttons.append(admin_btn)

    def on_tab_clicked(self, tab_name):
        # سيتم ربط هذه الإشارة من النافذة الرئيسية
        pass

    def update_texts(self):
        """تحديث النصوص عند تغيير اللغة"""
        tab_names = [
            ("lessons", tr("lessons")),
            ("speed_test", tr("speed_test")),
            ("practice_texts", tr("practice_texts"))
        ]
        
        for i, (tab_key, tab_label) in enumerate(tab_names):
            if i < len(self.tab_buttons):
                self.tab_buttons[i].setText(tab_label)
                
        if self.is_admin and len(self.tab_buttons) > 3:
            self.tab_buttons[3].setText(tr("admin_panel"))

    def update_tab_states(self, all_lessons_completed, completed_trainings):
        """تحديث حالة الأزرار بناءً على تقدم المستخدم"""
        # تمكين جميع التبويبات للمدير بغض النظر عن التقدم
        if self.is_admin:
            for btn in self.tab_buttons:
                btn.setEnabled(True)
                btn.setToolTip("")
        else:
            self.tab_buttons[0].setEnabled(True)
            self.tab_buttons[0].setToolTip("")
            
            self.tab_buttons[2].setEnabled(all_lessons_completed)
            if not all_lessons_completed:
                self.tab_buttons[2].setToolTip(tr("complete_all_lessons_first"))
            else:
                self.tab_buttons[2].setToolTip("")
            
            speed_enabled = len(completed_trainings) > 0
            self.tab_buttons[1].setEnabled(speed_enabled)
            if not speed_enabled:
                if not all_lessons_completed:
                    self.tab_buttons[1].setToolTip(tr("complete_all_training_first"))
                else:
                    self.tab_buttons[1].setToolTip(tr("complete_practice_first"))
            else:
                self.tab_buttons[1].setToolTip("")

        for btn in self.tab_buttons:
            btn.update()