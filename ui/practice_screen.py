import os
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QGridLayout, 
    QListWidget, QListWidgetItem, QFrame, QSizePolicy, QHBoxLayout
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QFont, QBrush, QColor
from utils.tr import tr
from utils.resource import resource_path

class PracticeScreen(QWidget):
    # إشارة للانتقال إلى شاشة التدريب
    switch_to_practice_runner = pyqtSignal(dict)
    
    def __init__(self, username, progress):
        super().__init__()  # استدعاء مُنشئ الفئة الأساسية
        
        self.username = username
        # التأكد من أن التقدم هو قاموس
        self.progress = progress if isinstance(progress, dict) else {}
        self.lang = "ar"
        self.texts = {}
        self.load_texts()
        
        # حالة اجتياز المستويات
        self.beginner_passed = False
        self.intermediate_passed = False
        self.current_level = None
        self.selected_text = None
        
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setSpacing(20)
        
        # عنوان الشاشة
        self.title_label = QLabel(tr("practice_title"))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #1e88e5;
            padding: 10px;
        """)
        main_layout.addWidget(self.title_label)
        
        # إطار المستويات
        self.levels_frame = QWidget()
        grid_layout = QGridLayout(self.levels_frame)
        grid_layout.setContentsMargins(20, 20, 20, 20)
        grid_layout.setSpacing(20)
        
        # أزرار المستويات
        self.beginner_btn = self.create_level_button("beginner")
        self.intermediate_btn = self.create_level_button("intermediate")
        self.advanced_btn = self.create_level_button("advanced")
        
        grid_layout.addWidget(self.beginner_btn, 0, 0)
        grid_layout.addWidget(self.intermediate_btn, 0, 1)
        grid_layout.addWidget(self.advanced_btn, 0, 2)
        
        main_layout.addWidget(self.levels_frame)
        
        # إطار قائمة العناوين
        self.titles_frame = QWidget()
        self.titles_frame.setVisible(False)
        titles_layout = QVBoxLayout(self.titles_frame)
        titles_layout.setSpacing(15)
        titles_layout.setContentsMargins(20, 20, 20, 20)
        
        # عنوان المستوى المحدد
        self.level_title = QLabel()
        self.level_title.setStyleSheet("""
            font-size: 22px; 
            font-weight: bold; 
            color: #1e88e5;
            padding: 10px;
            border-bottom: 2px solid #1e88e5;
        """)
        self.level_title.setAlignment(Qt.AlignCenter)
        titles_layout.addWidget(self.level_title)
        
        # قائمة العناوين
        self.titles_list = QListWidget()
        self.titles_list.setStyleSheet("""
            QListWidget {
                background-color: #f9f9f9;
                border-radius: 8px;
                padding: 10px;
                font-size: 16px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #e0e0e0;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1e88e5;
                font-weight: bold;
            }
            QListWidget::item:disabled {
                color: #bdbdbd;
                background-color: #f5f5f5;
            }
        """)
        self.titles_list.itemClicked.connect(self.handle_title_click)
        titles_layout.addWidget(self.titles_list)
        
        # زر بدء التمرين
        self.start_practice_btn = QPushButton(tr("start_practice"))
        self.start_practice_btn.setMinimumHeight(50)
        self.start_practice_btn.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                font-weight: bold;
                padding: 12px 24px;
                background-color: #43a047;
                color: white;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
            QPushButton:disabled {
                background-color: #a5d6a7;
                color: #e8f5e9;
            }
        """)
        self.start_practice_btn.setEnabled(False)
        self.start_practice_btn.clicked.connect(self.start_practice)
        titles_layout.addWidget(self.start_practice_btn, alignment=Qt.AlignCenter)
        
        main_layout.addWidget(self.titles_frame)
        
        # زر العودة إلى المستويات
        self.back_to_levels_btn = QPushButton(tr("back_button"))
        self.back_to_levels_btn.setMinimumWidth(120)
        self.back_to_levels_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                padding: 10px 20px;
                background-color: #1e88e5;
                color: white;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        self.back_to_levels_btn.clicked.connect(self.back_to_levels)
        main_layout.addWidget(self.back_to_levels_btn, alignment=Qt.AlignCenter)
        self.back_to_levels_btn.setVisible(False)
        
        self.setLayout(main_layout)
        self.update_texts()
        
        # تفعيل/تعطيل الأزرار
        self.beginner_btn.setEnabled(True)
        self.intermediate_btn.setEnabled(False)
        self.advanced_btn.setEnabled(False)
        
        # ربط الأحداث
        self.beginner_btn.clicked.connect(lambda: self.show_level_titles("beginner"))
        self.intermediate_btn.clicked.connect(lambda: self.show_level_titles("intermediate"))
        self.advanced_btn.clicked.connect(lambda: self.show_level_titles("advanced"))
        
        # تحديد اتجاه الواجهة
        self.update_direction()
    
    def update_progress(self, progress):
        """تحديث تقدم المستخدم"""
        # التأكد من أن التقدم هو قاموس
        self.progress = progress if isinstance(progress, dict) else {}
        
        # تحديث واجهة المستخدم حسب التقدم الجديد
        self.update_levels_availability()
        
        # إذا كان هناك مستوى معروض حاليًا، نقوم بتحديث قائمة العناوين
        if self.current_level:
            # إعادة تحميل القائمة فورًا
            self.refresh_title_list()
    
    def refresh_title_list(self):
        """إعادة تحميل قائمة العناوين مع الحفاظ على التحديد الحالي"""
        if self.current_level:
            # حفظ النص المحدد حالياً
            current_item = self.titles_list.currentItem()
            current_data = current_item.data(Qt.UserRole) if current_item else None
            current_id = current_data.get("id") if isinstance(current_data, dict) else None
            
            # إعادة تحميل القائمة
            self.show_level_titles(self.current_level)
            
            # استعادة التحديد إن أمكن
            if current_id is not None:
                for index in range(self.titles_list.count()):
                    item = self.titles_list.item(index)
                    item_data = item.data(Qt.UserRole)
                    if isinstance(item_data, dict) and item_data.get("id") == current_id:
                        self.titles_list.setCurrentItem(item)
                        self.handle_title_click(item)
                        break

    def has_next_text(self):
        if not self.current_level or not self.selected_text:
            return False

        texts = sorted(
            self.texts.get(self.current_level.lower(), []),
            key=lambda item: item.get("id", 0),
        )
        current_id = self.selected_text.get("id")
        return any(
            item.get("id") == current_id and index < len(texts) - 1
            for index, item in enumerate(texts)
        )
    
    def update_levels_availability(self):
        """تحديث توفر المستويات بناءً على تقدم المستخدم"""
        # تحميل النصوص المكتملة للغة الحالية
        completed_practice = self.progress.get("completed_practice", {})
        
        # إذا كان completed_practice قائمة، نحولها إلى قاموس
        if isinstance(completed_practice, list):
            # تحويل القائمة إلى قاموس مع افتراض أنها للغة الحالية
            completed_practice = {self.lang: completed_practice}
            # حفظ التنسيق الجديد في التقدم
            self.progress["completed_practice"] = completed_practice
        
        # الحصول على قائمة النصوص المكتملة للغة الحالية
        lang_completed = completed_practice.get(self.lang, [])
        
        # تفعيل المستوى المبتدئ (دائمًا متاح)
        self.beginner_btn.setEnabled(True)
        
        # تفعيل المستوى المتوسط إذا تم إكمال جميع نصوص المبتدئ
        beginner_texts = self.texts.get("beginner", [])
        beginner_completed = all(text_data.get("id") in lang_completed for text_data in beginner_texts)
        self.intermediate_btn.setEnabled(beginner_completed)
        
        # تفعيل المستوى المتقدم إذا تم إكمال جميع نصوص المتوسط
        intermediate_texts = self.texts.get("intermediate", [])
        intermediate_completed = all(text_data.get("id") in lang_completed for text_data in intermediate_texts)
        self.advanced_btn.setEnabled(intermediate_completed)
    
    def create_level_button(self, level):
        """إنشاء زر للمستوى"""
        btn = QPushButton(tr(f"{level}_level"))
        btn.setProperty("level", level)
        
        btn.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                padding: 20px;
                background-color: #0288d1;
                color: white;
                border-radius: 10px;
                min-width: 180px;
                min-height: 100px;
            }
            QPushButton:hover {
                background-color: #0277bd;
            }
            QPushButton:disabled {
                background-color: #b0bec5;
                color: #757575;
            }
        """)
        
        return btn
    
    def load_texts(self):
        """تحميل نصوص التدريب من ملفات JSON"""
        try:
            # تحديد ملف النصوص بناءً على اللغة
            lang_file = "practice_ar.json" if self.lang == "ar" else "practice_en.json"
            
            # استخدام resource_path للحصول على المسار الصحيح
            file_path = resource_path(os.path.join("data", lang_file))
            
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    # تحميل النصوص
                    raw_texts = json.load(f)
                    
                    # تحويل المفاتيح إلى حروف صغيرة لتوحيد التنسيق
                    self.texts = {
                        key.lower(): value for key, value in raw_texts.items()
                    }
            else:
                # استخدام ملف اللغة البديل إذا لم يوجد الملف
                fallback_lang = "en" if self.lang == "ar" else "ar"
                fallback_file = "practice_ar.json" if fallback_lang == "ar" else "practice_en.json"
                fallback_path = resource_path(os.path.join("data", fallback_file))
                
                if os.path.exists(fallback_path):
                    with open(fallback_path, "r", encoding="utf-8") as f:
                        raw_texts = json.load(f)
                        self.texts = {
                            key.lower(): value for key, value in raw_texts.items()
                        }
                else:
                    self.texts = {}
        except Exception as e:
            print(f"Error loading texts: {e}")
            self.texts = {}
    
    def update_texts(self):
        """تحديث النصوص بناءً على اللغة المحددة"""
        self.title_label.setText(tr("practice_title"))
        self.back_to_levels_btn.setText(tr("back_button"))
        self.start_practice_btn.setText(tr("start_practice"))
        
        # تحديث نصوص الأزرار
        self.beginner_btn.setText(tr("beginner_level"))
        self.intermediate_btn.setText(tr("intermediate_level"))
        self.advanced_btn.setText(tr("advanced_level"))
    
    def update_language(self, lang):
        """تحديث اللغة للشاشة"""
        self.lang = lang
        self.load_texts()
        self.update_texts()
        self.update_direction()
        
        # تحديث العرض الحالي إذا كان معروضاً
        if self.titles_frame.isVisible() and self.current_level:
            self.show_level_titles(self.current_level)
    
    def update_direction(self):
        """تحديث اتجاه الواجهة حسب اللغة"""
        if self.lang == "ar":
            self.setLayoutDirection(Qt.RightToLeft)
            self.titles_list.setLayoutDirection(Qt.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LeftToRight)
            self.titles_list.setLayoutDirection(Qt.LeftToRight)
    
    def show_level_titles(self, level):
        """عرض قائمة بعناوين نصوص المستوى المحدد"""
        self.current_level = level
        level_key = level.lower()
        
        # إخفاء إطار المستويات وإظهار إطار العناوين
        self.levels_frame.setVisible(False)
        self.titles_frame.setVisible(True)
        self.back_to_levels_btn.setVisible(True)
        
        # تحديث عنوان المستوى
        self.level_title.setText(tr(f"{level}_level"))
        
        # مسح القائمة الحالية
        self.titles_list.clear()
        self.start_practice_btn.setEnabled(False)
        self.selected_text = None
        
        # التحقق من وجود نصوص للمستوى المحدد
        if self.texts.get(level_key) and isinstance(self.texts[level_key], list) and len(self.texts[level_key]) > 0:
            # ترتيب النصوص حسب الـ ID
            sorted_texts = sorted(self.texts[level_key], key=lambda x: x.get('id', 0))
            
            # الحصول على النصوص المكتملة للغة الحالية
            completed_practice = self.progress.get("completed_practice", {})
            
            # إذا كان completed_practice قائمة، نحولها إلى قاموس
            if isinstance(completed_practice, list):
                completed_practice = {self.lang: completed_practice}
                self.progress["completed_practice"] = completed_practice
            
            # الحصول على النصوص المكتملة لهذا المستوى للغة الحالية
            lang_completed = completed_practice.get(self.lang, [])
            
            # إضافة العناوين إلى القائمة
            for i, text_data in enumerate(sorted_texts):
                text_id = text_data.get("id")
                title = text_data.get("title", tr("untitled_text"))
                
                # إضافة علامة نجاح إذا تم إكمال النص
                if text_id in lang_completed:
                    title = "✓ " + title
                
                item = QListWidgetItem(title)
                item.setData(Qt.UserRole, text_data)
                
                # تمكين النص إذا كان الأول أو إذا تم إكمال النص السابق
                prev_text_completed = True
                if i > 0:
                    prev_text_id = sorted_texts[i-1].get("id")
                    prev_text_completed = prev_text_id in lang_completed
                
                if i == 0 or prev_text_completed:
                    item.setFlags(item.flags() | Qt.ItemIsEnabled)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                    item.setData(Qt.UserRole, None)  # لا تخزّن بيانات للنصوص المعطلة
                    item.setForeground(QBrush(QColor(150, 150, 150)))  # لون رمادي للنصوص المعطلة
                
                # تحديد لون النص
                if text_id in lang_completed:
                    item.setForeground(QBrush(QColor(0, 128, 0)))  # لون أخضر للنصوص المكتملة
                elif item.flags() & Qt.ItemIsEnabled:
                    item.setForeground(QBrush(QColor(0, 0, 0)))  # لون أسود للنصوص العادية
                
                self.titles_list.addItem(item)
            
            # تفعيل العنصر الأول الممكن وتحديده
            for i in range(self.titles_list.count()):
                item = self.titles_list.item(i)
                if item.flags() & Qt.ItemIsEnabled:
                    item.setSelected(True)
                    self.handle_title_click(item)
                    break
        else:
            # إذا لم توجد نصوص للمستوى المحدد
            item = QListWidgetItem(tr("no_texts_message").format(level=tr(f"{level}_level")))
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            self.titles_list.addItem(item)
    
    def handle_title_click(self, item):
        """معالجة النقر على عنوان نص"""
        # الحصول على بيانات النص من UserRole
        text_data = item.data(Qt.UserRole)
        
        if text_data:
            self.selected_text = text_data
            self.start_practice_btn.setEnabled(True)
    
    def start_practice(self):
        """بدء التمرين بالانتقال إلى شاشة PracticeRunner"""
        if self.selected_text:
            # إضافة اللغة إلى بيانات النص
            text_data = self.selected_text.copy()
            text_data["lang"] = self.lang
            
            # إطلاق إشارة للانتقال إلى شاشة التدريب مع النص المحدد
            self.switch_to_practice_runner.emit(text_data)
    
    def back_to_levels(self):
        """العودة إلى قائمة المستويات"""
        self.titles_frame.setVisible(False)
        self.levels_frame.setVisible(True)
        self.back_to_levels_btn.setVisible(False)
        
        # تحديث حالة المستويات بناءً على التقدم الحالي
        self.update_levels_availability()
        
        # إعادة تعيين الحالة
        self.current_level = None
        self.selected_text = None
        self.start_practice_btn.setEnabled(False)