# admin_panel/lesson_manager.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QApplication, QTextEdit, QListWidget, QListWidgetItem, QMessageBox, QHBoxLayout, QComboBox, QFileDialog, QSplitter, QFrame, QShortcut
from PyQt5.QtCore import Qt, QEvent, QTimer
from PyQt5.QtGui import QTextCursor, QKeySequence
import json
import os
from utils.tr import tr
from utils.resource import resource_path, user_data_path

class FocusableTextEdit(QTextEdit):
    """نسخة مخصصة من QTextEdit مع حل مشكلة التركيز"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        
    def keyPressEvent(self, event):
        # تمرير جميع أحداث لوحة المفاتيح للمحرر حتى لو لم يكن التركيز عليه
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        # تمرير جميع أحداث تحرير المفاتيح للمحرر
        super().keyReleaseEvent(event)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)

class AdminLessonManager(QWidget):
    def set_focus(self):
        """تعيين التركيز على المحرر الرئيسي (متوافقة مع استدعاءات main_window)"""
        self.force_focus_editor()
    def showEvent(self, event):
        """عند عرض واجهة الأدمن يتم إعادة تحميل الدروس دائماً من ملف json"""
        self.load_lessons()
        super().showEvent(event)
    def __init__(self, json_path=None):
        super().__init__()
        self.setWindowTitle("لوحة تحكم الأدمن - إدارة الدروس")
        # اجعل الواجهة مرنة
        
        # تحديد مسار ملف الدروس
        # اختيار ملف الدروس الصحيح بناءً على الملفات الفعلية في المشروع
        # لا تقبل إلا الملفات الفعلية lessons_ar.json أو lessons_en.json أو ملف يختاره المستخدم
        allowed_files = ["data/lessons_ar.json", "data/lessons_en.json"]
        if json_path and isinstance(json_path, str) and json_path.replace("\\", "/") in allowed_files:
            self.lessons_path = user_data_path(json_path)
        elif json_path and isinstance(json_path, str) and os.path.exists(resource_path(json_path)):
            self.lessons_path = resource_path(json_path)
        else:
            found = False
            for f in allowed_files:
                full_path = user_data_path(f)
                if os.path.exists(full_path):
                    self.lessons_path = full_path
                    found = True
                    break
            if not found:
                self.lessons_path = None  # لا يوجد ملف دروس فعلي
        self.lessons = {}
        self.current_lesson = None
        self.current_group = None
        self.current_field = "title"
        self.suppress_selection_event = False

        # إنشاء التصميم الرئيسي
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # قسم القائمة والتحكم
        left_frame = QFrame()
        left_frame.setFrameShape(QFrame.StyledPanel)
        left_layout = QVBoxLayout(left_frame)

        # أزرار فتح الملف
        file_btn_layout = QHBoxLayout()
        btn_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1976d2, stop:1 #64b5f6);
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 18px;
                padding: 10px 0;
                margin-bottom: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1565c0, stop:1 #42a5f5);
            }
        """
        self.open_file_btn = QPushButton("📂   اختار ملف ")
        self.open_file_btn.setStyleSheet(btn_style)
        self.open_file_btn.clicked.connect(self.open_json_file)
        file_btn_layout.addWidget(self.open_file_btn)
        left_layout.addLayout(file_btn_layout)

        # قائمة الدروس
        left_layout.addWidget(QLabel("📋 قائمة الدروس"))
        self.lesson_list = QListWidget()
        self.lesson_list.setStyleSheet("font-size: 14px;")
        self.lesson_list.currentRowChanged.connect(self.load_selected_lesson)
        left_layout.addWidget(self.lesson_list)

        # إضافة أزرار التحكم
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 حفظ التعديلات")
        self.save_btn.setStyleSheet(btn_style)
        self.save_btn.clicked.connect(self.save_changes)
        btn_layout.addWidget(self.save_btn)

        self.add_btn = QPushButton("➕ إضافة درس")
        self.add_btn.setStyleSheet(btn_style)
        self.add_btn.clicked.connect(self.add_lesson)
        btn_layout.addWidget(self.add_btn)

        self.delete_btn = QPushButton("🗑️ حذف الدرس")
        self.delete_btn.setStyleSheet(btn_style)
        self.delete_btn.clicked.connect(self.delete_lesson)
        btn_layout.addWidget(self.delete_btn)

        left_layout.addLayout(btn_layout)

        # قسم تحرير المحتوى
        right_frame = QFrame()
        right_frame.setFrameShape(QFrame.StyledPanel)
        right_layout = QVBoxLayout(right_frame)

        # القائمة المنسدلة لاختيار الحقل
        right_layout.addWidget(QLabel("<b>اختر حقل للتعديل:</b>"))
        self.field_selector = QComboBox()
        self.field_selector.setStyleSheet("font-size: 14px; padding: 8px;")
        self.field_selector.addItems(["العنوان", "الوصف", "المحتوى"])
        self.field_selector.currentIndexChanged.connect(self.change_field)
        right_layout.addWidget(self.field_selector)

        # استخدام النسخة المخصصة من QTextEdit لحل مشكلة التركيز
        self.editor = FocusableTextEdit()
        self.editor.setReadOnly(False)
        self.editor.setFocusPolicy(Qt.StrongFocus)
        self.editor.setAcceptRichText(True)
        self.editor.setStyleSheet("""
            QTextEdit {
                font-size: 16px;
                background-color: white;
                border: 2px solid #ccc;
                padding: 15px;
                border-radius: 5px;
            }
        """)
        self.editor.textChanged.connect(self.update_current_field)
        right_layout.addWidget(self.editor, 1)
        
        # تلميحات اختصارات لوحة المفاتيح
        shortcuts_label = QLabel(
            "اختصارات لوحة المفاتيح:\n"
            "• Ctrl+C: نسخ • Ctrl+V: لصق • Ctrl+X: قص\n"
            "• Ctrl+Z: تراجع • Ctrl+Y: إعادة • Ctrl+S: حفظ\n"
            "• Tab: التنقل بين العناصر • Enter: تحرير العنصر المحدد"
        )
        shortcuts_label.setStyleSheet("""
            font-size: 12px; 
            color: #666; 
            padding: 10px; 
            background: #f8f8f8; 
            border-radius: 5px;
            margin-top: 10px;
        """)
        right_layout.addWidget(shortcuts_label)

        # إضافة الأقسام إلى التصميم الرئيسي
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_frame)
        splitter.addWidget(right_frame)
        splitter.setSizes([400, 800])
        main_layout.addWidget(splitter)

        # إعداد اختصارات لوحة المفاتيح
        self.setup_keyboard_shortcuts()
        
        # تثبيت مرشح الأحداث لمعالجة تنشيط النافذة
        self.installEventFilter(self)
        
        # تحميل الدروس
        self.load_lessons()

    def setup_keyboard_shortcuts(self):
        """تهيئة جميع اختصارات لوحة المفاتيح"""
        # اختصارات النسخ/لصق/قص
        QShortcut(QKeySequence.Copy, self.editor, self.editor.copy)
        QShortcut(QKeySequence.Paste, self.editor, self.editor.paste)
        QShortcut(QKeySequence.Cut, self.editor, self.editor.cut)
        
        # اختصارات التراجع والإعادة
        QShortcut(QKeySequence.Undo, self.editor, self.editor.undo)
        QShortcut(QKeySequence.Redo, self.editor, self.editor.redo)
        
        # اختصار الحفظ
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_changes)
        
        # اختصارات التنقل
        QShortcut(QKeySequence(Qt.Key_Tab), self, self.focus_next_widget)
        QShortcut(QKeySequence("Shift+Tab"), self, self.focus_previous_widget)
        
        # اختصارات قائمة الدروس
        QShortcut(QKeySequence(Qt.Key_Up), self, lambda: self.navigate_lesson_list(-1))
        QShortcut(QKeySequence(Qt.Key_Down), self, lambda: self.navigate_lesson_list(1))
        QShortcut(QKeySequence(Qt.Key_Return), self, self.select_current_lesson)
        QShortcut(QKeySequence(Qt.Key_Enter), self, self.select_current_lesson)
        
        # اختصار للانتقال إلى المحرر
        QShortcut(QKeySequence("Ctrl+E"), self, self.force_focus_editor)
        
        # تمكين القائمة السياقية للمحرر
        self.editor.setContextMenuPolicy(Qt.DefaultContextMenu)

    def open_json_file(self):
        """فتح ملف JSON خارجي"""
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "اختر ملف JSON", 
            "", 
            "JSON Files (*.json)"
        )
        
        if path:
            self.lessons_path = path
            self.load_lessons()
            QMessageBox.information(
                self,
                "تم التحميل",
                f"تم تحميل ملف الدروس بنجاح:\n{path}"
            )
            # التركيز على المحرر بعد التحميل
            QTimer.singleShot(100, self.force_focus_editor)

    def focus_next_widget(self):
        """الانتقال للعنصر التالي في الواجهة"""
        self.focusNextChild()

    def focus_previous_widget(self):
        """الانتقال للعنصر السابق في الواجهة"""
        self.focusPreviousChild()
    
    def force_focus_editor(self):
        """إجبار التركيز على المحرر"""
        if self.editor.isEnabled():
            self.editor.setFocus(Qt.ActiveWindowFocusReason)
            self.editor.activateWindow()
            self.editor.raise_()
            
            # نقل المؤشر لنهاية النص
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.editor.setTextCursor(cursor)
    
    def navigate_lesson_list(self, direction):
        """التنقل في قائمة الدروس باستخدام الأسهم"""
        current_row = self.lesson_list.currentRow()
        new_row = current_row + direction
        
        if new_row < 0:
            new_row = self.lesson_list.count() - 1
        elif new_row >= self.lesson_list.count():
            new_row = 0
            
        self.lesson_list.setCurrentRow(new_row)
    
    def select_current_lesson(self):
        """تحديد الدرس الحالي في القائمة"""
        current_row = self.lesson_list.currentRow()
        if current_row >= 0:
            self.load_selected_lesson(current_row)
            self.force_focus_editor()

    def enable_editing(self, enabled):
        """تمكين/تعطيل عناصر التحرير فقط (لا تحفظ حالة enabled تلقائياً)"""
        self.save_btn.setEnabled(enabled)
        self.add_btn.setEnabled(enabled)
        self.delete_btn.setEnabled(enabled)
        self.editor.setEnabled(enabled)
        self.editor.setReadOnly(not enabled)
        if enabled:
            self.force_focus_editor()

    def change_field(self, index):
        """تغيير الحقل النشط للتحرير"""
        if not self.current_lesson:
            self.editor.clear()
            return
            
        if index == 0:
            self.current_field = "title"
            value = self.current_lesson.get("title", "")
        elif index == 1:
            self.current_field = "description"
            value = self.current_lesson.get("description", "")
        elif index == 2:
            self.current_field = "content"
            value = self.current_lesson.get("content", "")
        
        if not value:
            if self.current_field == "description":
                value = "لا يوجد وصف"
            elif self.current_field == "content":
                value = "لا يوجد محتوى"
        
        self.editor.setPlainText(value)
        self.force_focus_editor()

    def update_current_field(self):
        """تحديث الحقل النشط عند التعديل"""
        if not self.current_lesson:
            return
            
        new_value = self.editor.toPlainText()
        
        if new_value in ["لا يوجد وصف", "لا يوجد محتوى"]:
            new_value = ""
        
        self.current_lesson[self.current_field] = new_value
        self.update_current_lesson_in_list()

    def load_lessons(self):
        """تحميل الدروس من ملف JSON"""
        print(f"[DEBUG] Trying to load lessons from: {self.lessons_path}")
        if not self.lessons_path or not os.path.exists(self.lessons_path):
            print(f"[ERROR] File not found: {self.lessons_path}")
            QMessageBox.warning(self, "خطأ", f"ملف الدروس غير موجود: {self.lessons_path}")
            return

        try:
            with open(self.lessons_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except Exception as e:
            error_msg = f"حدث خطأ أثناء قراءة الملف:\n{str(e)}"
            QMessageBox.critical(self, "خطأ", error_msg)
            return

        # إعادة هيكلة البيانات
        self.lessons = {}
        
        if isinstance(raw_data, list):
            self.lessons["غير مصنفة"] = raw_data
        elif isinstance(raw_data, dict):
            if "lessons" in raw_data and isinstance(raw_data["lessons"], list):
                self.lessons["غير مصنفة"] = raw_data["lessons"]
            else:
                self.lessons = raw_data
        else:
            error_msg = "بنية الملف غير مدعومة."
            QMessageBox.critical(self, "خطأ", error_msg)
            return

        self.update_lesson_list()
        # التركيز على المحرر بعد التحميل
        QTimer.singleShot(100, self.force_focus_editor)

    def update_lesson_list(self):
        """تحديث قائمة الدروس"""
        # حفظ التحديد الحالي
        current_index = self.lesson_list.currentRow()
        
        self.lesson_list.clear()

        for group, lessons in self.lessons.items():
            for lesson in lessons:
                title = lesson.get("title", "بدون عنوان")
                description = lesson.get("description", "")
                content = lesson.get("content", "")
                
                # إنشاء عنصر القائمة
                item_text = f"【{group}】{title}"
                if description:
                    item_text += f"\n- {description[:100]}"
                elif content:
                    item_text += f"\n- {str(content)[:100]}"
                else:
                    item_text += "\n- لا يوجد وصف أو محتوى"

                item = QListWidgetItem(item_text)
                # تخزين مرجع للدرس والمجموعة
                item.setData(Qt.UserRole, {"lesson": lesson, "group": group})
                self.lesson_list.addItem(item)
        
        # استعادة التحديد السابق إذا كان صالحاً
        if current_index >= 0 and current_index < self.lesson_list.count():
            self.lesson_list.setCurrentRow(current_index)
        else:
            # إذا لم يكن هناك تحديد، قم بتحديد العنصر الأول
            if self.lesson_list.count() > 0:
                self.lesson_list.setCurrentRow(0)
                self.load_selected_lesson(0)

    def update_current_lesson_in_list(self):
        """تحديث العنصر الحالي فقط في القائمة"""
        if not self.current_lesson or not self.current_group:
            return
            
        current_index = self.lesson_list.currentRow()
        if current_index < 0:
            return
            
        item = self.lesson_list.item(current_index)
        if not item:
            return
            
        title = self.current_lesson.get("title", "بدون عنوان")
        description = self.current_lesson.get("description", "")
        content = self.current_lesson.get("content", "")
        
        # إنشاء نص جديد للعنصر
        item_text = f"【{self.current_group}】{title}"
        if description:
            item_text += f"\n- {description[:100]}"
        elif content:
            item_text += f"\n- {str(content)[:100]}"
        else:
            item_text += "\n- لا يوجد وصف أو محتوى"

        # تحديث النص فقط
        item.setText(item_text)

    def load_selected_lesson(self, index):
        """تحميل الدرس المحدد"""
        # تجنب معالجة الأحداث أثناء التحديد
        if self.suppress_selection_event:
            return
            
        if index < 0:
            self.current_lesson = None
            self.current_group = None
            self.enable_editing(False)
            self.editor.clear()
            return

        item = self.lesson_list.item(index)
        if not item:
            return
        data = item.data(Qt.UserRole)
        if not data:
            QMessageBox.warning(self, "تحذير", "لا توجد بيانات لهذا العنصر.")
            return
        group = data["group"]
        lesson_id = data["lesson"].get("id")
        # ابحث عن العنصر الأصلي في self.lessons[group] بالمعرف
        lesson_ref = None
        for l in self.lessons.get(group, []):
            if l.get("id") == lesson_id:
                lesson_ref = l
                break
        if lesson_ref is None:
            # fallback: استخدم الداتا كما هي
            lesson_ref = data["lesson"]
        self.current_lesson = lesson_ref
        self.current_group = group
        
        # تفعيل التحرير
        self.enable_editing(True)
        
        # تحميل الحقل الأول (العنوان) في المحرر
        self.suppress_selection_event = True  # منع إعادة التحديد
        self.field_selector.setCurrentIndex(0)
        self.suppress_selection_event = False  # إعادة تفعيل الأحداث
        
        # عرض محتوى الحقل مباشرة
        self.change_field(0)
        # التركيز على المحرر بعد التحميل
        QTimer.singleShot(100, self.force_focus_editor)

    def save_changes(self):
        """حفظ التغييرات في الملف مع حفظ حالة التفعيل"""
        if not self.current_lesson:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد درس للحفظ.")
            return

        # تحديث القيم من المحرر
        self.update_current_field()

        # حفظ حالة التفعيل الحالية (enabled) في الدرس الحالي
        if self.current_lesson is not None:
            self.current_lesson['enabled'] = self.editor.isEnabled()

        # حفظ الملف
        self.save_to_file()

        QMessageBox.information(self, "تم", "تم حفظ التعديلات بنجاح.")

    def add_lesson(self):
        """إضافة درس جديد مع تفعيل الدرس افتراضياً"""
        new_lesson = {
            "title": "درس جديد",
            "description": "",
            "content": "",
            "enabled": True
        }
        if "غير مصنفة" not in self.lessons:
            self.lessons["غير مصنفة"] = []
        self.lessons["غير مصنفة"].append(new_lesson)
        self.save_to_file()
        self.update_lesson_list()
        last_index = self.lesson_list.count() - 1
        if last_index >= 0:
            self.lesson_list.setCurrentRow(last_index)
            self.load_selected_lesson(last_index)
        QMessageBox.information(self, "تم", "تم إضافة درس جديد.")
        QTimer.singleShot(100, self.force_focus_editor)

    def delete_lesson(self):
        """حذف درس محدد مع تحديث ملف json فوراً"""
        index = self.lesson_list.currentRow()
        if index < 0:
            QMessageBox.warning(self, "تحذير", "لم يتم تحديد درس للحذف.")
            return
        item = self.lesson_list.item(index)
        if not item:
            return
        data = item.data(Qt.UserRole)
        if not data:
            return
        lesson_data = data["lesson"]
        group = data["group"]
        reply = QMessageBox.question(
            self, "تأكيد الحذف", 
            f"هل أنت متأكد من حذف الدرس '{lesson_data['title']}'؟", 
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.lessons[group] = [l for l in self.lessons[group] if l != lesson_data]
            if not self.lessons[group]:
                del self.lessons[group]
            self.save_to_file()
            self.update_lesson_list()
            self.current_lesson = None
            self.enable_editing(False)
            self.editor.clear()

    def save_to_file(self):
        """حفظ البيانات إلى ملف JSON المختار فقط مع حماية وظهور رسالة باسم الملف"""
        if not self.lessons_path or not os.path.exists(self.lessons_path):
            QMessageBox.warning(self, "خطأ", "لم يتم اختيار ملف دروس صالح للحفظ. الرجاء اختيار ملف JSON أولاً.")
            return
        # تأكد من أن كل درس يحتوي على حقل enabled
        for group, lessons in self.lessons.items():
            for lesson in lessons:
                if 'enabled' not in lesson:
                    lesson['enabled'] = True  # افتراضي: مفعل
        try:
            with open(self.lessons_path, "w", encoding="utf-8") as f:
                json.dump(self.lessons, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "تم الحفظ", f"تم حفظ التعديلات في الملف:\n{self.lessons_path}")
        except Exception as e:
            error_msg = f"فشل حفظ الملف:\n{str(e)}"
            QMessageBox.critical(self, "خطأ", error_msg)
    
    def eventFilter(self, obj, event):
        """تصفية الأحداث لمعالجة تنشيط النافذة"""
        if event.type() == QEvent.WindowActivate:
            # عند تنشيط النافذة، إعادة التركيز على المحرر
            QTimer.singleShot(50, self.force_focus_editor)
            return True
        return super().eventFilter(obj, event)

    def load_lessons(self):
        """تحميل الدروس من ملف JSON مع قراءة حالة التفعيل"""
        if not self.lessons_path:
            QMessageBox.warning(self, "خطأ", "لم يتم تحديد أي ملف دروس. الرجاء اختيار ملف صحيح.")
            return
        if not os.path.exists(self.lessons_path):
            # حماية إضافية: إذا كان اسم الملف غير lessons_ar.json أو lessons_en.json أو ملف اختاره المستخدم، لا تحاول التحميل
            allowed_files = [
                user_data_path("data/lessons_ar.json"),
                user_data_path("data/lessons_en.json"),
            ]
            if self.lessons_path not in allowed_files and not os.path.exists(self.lessons_path):
                msg = f"ملف الدروس غير موجود فعلياً:\n{self.lessons_path}\nيرجى التأكد من اسم الملف أو اختياره من جديد."
                QMessageBox.warning(self, "خطأ", msg)
                print(f"[ERROR] lessons_path does not exist: {self.lessons_path}")
                return

        try:
            with open(self.lessons_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except Exception as e:
            error_msg = f"حدث خطأ أثناء قراءة الملف:\n{str(e)}"
            QMessageBox.critical(self, "خطأ", error_msg)
            return

        # إعادة هيكلة البيانات
        self.lessons = {}
        if isinstance(raw_data, list):
            self.lessons["غير مصنفة"] = raw_data
        elif isinstance(raw_data, dict):
            if "lessons" in raw_data and isinstance(raw_data["lessons"], list):
                self.lessons["غير مصنفة"] = raw_data["lessons"]
            else:
                self.lessons = raw_data
        else:
            error_msg = "بنية الملف غير مدعومة."
            QMessageBox.critical(self, "خطأ", error_msg)
            return

        # تأكد من وجود حقل enabled في كل درس
        for group, lessons in self.lessons.items():
            for lesson in lessons:
                if 'enabled' not in lesson:
                    lesson['enabled'] = True

        self.update_lesson_list()
        # التركيز على المحرر بعد التحميل
        QTimer.singleShot(100, self.force_focus_editor)
    # كود الاختبار التجريبي تم حذفه لتفادي أخطاء التنسيق عند الاستيراد من main.py