# محرر النصوص الثابتة في التطبيق
import os
import json
import shutil
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLineEdit, QLabel, QComboBox,
    QAbstractItemView, QMessageBox, QMenu, QAction, QSizePolicy, QApplication
)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QColor
from utils.tr import tr
from utils.resource import resource_path, user_data_directory, user_data_path
import traceback
import logging
import sys

# إعداد نظام التسجيل
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('static_texts_editor.log'),
        logging.StreamHandler()
    ]
)

class StaticTextsEditor(QWidget):
    def __init__(self, translation_manager, parent=None):
        super().__init__(parent)
        self.translation_manager = translation_manager
        self.setWindowTitle(tr("static_text_editor"))
        self.setMinimumSize(600, 400)
        self.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Expanding)
        self.is_initialized = False
        self.current_data = {"ar": {}, "en": {}}
        
        self.apply_stylesheet()
        self.setup_ui()
        self.create_backup()
        self.load_data()
        self.is_initialized = True

    def apply_stylesheet(self):
        qss_path = resource_path(os.path.join("styles", "app.qss"))
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        top_bar = QHBoxLayout()
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["ar", "en"])
        self.lang_combo.setCurrentIndex(0)
        self.lang_combo.setFixedWidth(80)
        top_bar.addWidget(QLabel(tr("language") + ":"))
        top_bar.addWidget(self.lang_combo)

        self.add_btn = self.create_button(tr("add_key"), self.add_new_key)
        self.save_btn = self.create_button(tr("save"), self.save_changes)
        self.delete_btn = self.create_button(tr("delete"), self.delete_selected_key)
        self.reload_btn = self.create_button(tr("reload_static_texts"), self.reload_static_texts)
        top_bar.addWidget(self.add_btn)
        top_bar.addWidget(self.save_btn)
        top_bar.addWidget(self.delete_btn)
        top_bar.addWidget(self.reload_btn)
        top_bar.addSpacing(8)
        top_bar.addWidget(QLabel(tr("search") + ":"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("search_placeholder"))
        self.search_input.textChanged.connect(self.filter_table)
        self.search_input.setMinimumWidth(300)
        self.search_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        top_bar.addWidget(self.search_input)
        self.unused_btn = self.create_button(tr("show_unused_keys"), self.filter_unused_keys)
        self.clear_filter_btn = self.create_button(tr("clear_filter"), self.clear_filters)
        top_bar.addWidget(self.unused_btn)
        top_bar.addWidget(self.clear_filter_btn)
        main_layout.addLayout(top_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([tr("key"), tr("arabic"), tr("english")])
        self.table.setColumnWidth(0, 120)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.setMinimumHeight(400)
        self.table.setMinimumWidth(800)
        self.table.setStyleSheet("QTableWidget::item { padding: 2px; } QLineEdit { padding: 2px; }")
        main_layout.addWidget(self.table, 1)

        self.status_bar = QLabel()
        main_layout.addWidget(self.status_bar)

    def create_button(self, text, callback):
        btn = QPushButton(text)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.clicked.connect(callback)
        return btn

    def get_writable_translation_path(self, lang):
        """الحصول على مسار ملف الترجمة القابل للكتابة"""
        return user_data_path(os.path.join("data", "translations", f"{lang}.json"))

    def create_backup(self):
        backup_dir = user_data_directory("data", "backups")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for lang in ["ar", "en"]:
            src_file = self.get_writable_translation_path(lang)
            if os.path.exists(src_file):
                backup_file = os.path.join(backup_dir, f"static_strings_{lang}_{timestamp}.json")
                shutil.copy2(src_file, backup_file)
                self.update_status(tr("backup_created").format(lang=lang, path=backup_file))
                logging.info(f"Backup created: {backup_file}")

    def load_data(self):
        """تحميل البيانات من ملفات الترجمة وعرضها في الجدول"""
        try:
            # مسح الجدول الحالي
            self.table.clearContents()
            self.table.setRowCount(0)
            
            # تحميل البيانات
            ar_trans = self.load_translation_file('ar')
            en_trans = self.load_translation_file('en')
            
            # حفظ البيانات الحالية
            self.current_data = {"ar": ar_trans, "en": en_trans}
            
            # دمج المفاتيح من اللغتين
            all_keys = sorted(set(list(ar_trans.keys()) + list(en_trans.keys())))
            logging.info(f"Total keys found: {len(all_keys)}")
            
            # تعبئة الجدول بالبيانات
            self.table.setRowCount(len(all_keys))
            for row, key in enumerate(all_keys):
                # العمود 0: المفتاح
                key_item = QTableWidgetItem(key)
                key_item.setFlags(key_item.flags() | Qt.ItemIsEditable)
                self.table.setItem(row, 0, key_item)
                
                # العمود 1: النص العربي
                ar_item = QTableWidgetItem(ar_trans.get(key, ""))
                ar_item.setFlags(ar_item.flags() | Qt.ItemIsEditable)
                self.table.setItem(row, 1, ar_item)
                
                # العمود 2: النص الإنجليزي
                en_item = QTableWidgetItem(en_trans.get(key, ""))
                en_item.setFlags(en_item.flags() | Qt.ItemIsEditable)
                self.table.setItem(row, 2, en_item)
            
            # تحديث حالة الواجهة
            self.update_status(tr("file_loaded").format(count=len(all_keys)))
            logging.info("Data loaded into table successfully")
            
            # إعادة تطبيق أي تصفية كانت مفعلة
            self.filter_table(self.search_input.text())
            
            return True
        except Exception as e:
            error_msg = f"Error loading translation data: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            QMessageBox.critical(self, tr("error"), error_msg)
            return False

    def load_translation_file(self, lang):
        """تحميل ملف ترجمة معين"""
        file_path = self.get_writable_translation_path(lang)
        logging.info(f"Loading {lang} from: {file_path}")
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logging.info(f"Loaded {len(data)} {lang} translations")
                    return data
            except Exception as e:
                logging.error(f"Error loading {lang} file: {str(e)}")
                # إنشاء ملف جديد إذا كان تالفاً
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)
                return {}
        else:
            # إنشاء ملف جديد إذا لم يكن موجوداً
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
            logging.info(f"Created new translation file: {file_path}")
            return {}

    def update_status(self, message):
        self.status_bar.setText(message)

    def add_new_key(self):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        key_item = QTableWidgetItem(f"new_key_{row_position + 1}")
        key_item.setBackground(QColor(255, 255, 200))
        self.table.setItem(row_position, 0, key_item)
        self.table.setItem(row_position, 1, QTableWidgetItem(""))
        self.table.setItem(row_position, 2, QTableWidgetItem(""))
        self.table.scrollToItem(key_item)
        self.table.editItem(key_item)
        self.update_status(tr("new_key_added"))
        logging.info("New key added")

    def save_changes(self):
        """حفظ التغييرات في ملفات الترجمة"""
        try:
            # جمع البيانات من الجدول
            ar_trans = {}
            en_trans = {}
            
            for row in range(self.table.rowCount()):
                key_item = self.table.item(row, 0)
                ar_item = self.table.item(row, 1)
                en_item = self.table.item(row, 2)
                
                if key_item and key_item.text().strip():
                    key = key_item.text().strip()
                    ar_value = ar_item.text().strip() if ar_item and ar_item.text() else ""
                    en_value = en_item.text().strip() if en_item and en_item.text() else ""
                    
                    ar_trans[key] = ar_value
                    en_trans[key] = en_value
            
            # حفظ البيانات
            self.save_translation_file('ar', ar_trans)
            self.save_translation_file('en', en_trans)
            
            # حفظ البيانات الحالية للتحديث
            self.current_data = {"ar": ar_trans, "en": en_trans}
            
            # إعادة تحميل الترجمات في التطبيق
            if hasattr(self.translation_manager, "reload_static_strings"):
                self.translation_manager.reload_static_strings()
            
            self.update_status(tr("changes_saved_successfully"))
            QMessageBox.information(self, tr("success"), tr("changes_saved_successfully_msg"))
            logging.info(f"Changes saved successfully: {len(ar_trans)} entries")
        except Exception as e:
            error_msg = tr("save_error_msg").format(str(e))
            logging.error(f"Save error: {error_msg}")
            logging.error(traceback.format_exc())
            QMessageBox.critical(self, tr("error"), error_msg)

    def save_translation_file(self, lang, data):
        """حفظ بيانات الترجمة في ملف"""
        file_path = self.get_writable_translation_path(lang)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Saved {lang} translations to {file_path}")

    def delete_selected_key(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            key = self.table.item(selected_row, 0).text() if self.table.item(selected_row, 0) else ""
            reply = QMessageBox.question(
                self, tr("confirm_delete"),
                tr("confirm_delete_msg").format(key if key else tr("empty_key")),
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # حذف المفتاح من البيانات الحالية
                if key in self.current_data["ar"]:
                    del self.current_data["ar"][key]
                if key in self.current_data["en"]:
                    del self.current_data["en"][key]
                
                # حفظ التغييرات
                self.save_translation_file('ar', self.current_data["ar"])
                self.save_translation_file('en', self.current_data["en"])
                
                # إزالة الصف من الجدول
                self.table.removeRow(selected_row)
                self.update_status(tr("key_deleted").format(key=key if key else tr("empty_key")))
                logging.info(f"Key deleted: {key}")

    def copy_selected_key(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            key = self.table.item(selected_row, 0).text()
            ar_val = self.table.item(selected_row, 1).text()
            clipboard = QApplication.clipboard()
            clipboard.setText(f"{key}: {ar_val}")
            self.update_status(tr("key_copied").format(key=key))
            logging.info(f"Key copied: {key}")

    def reload_static_texts(self):
        """إعادة تحميل النصوص الثابتة من الملفات وتحديث الجدول"""
        try:
            # إعادة تحميل البيانات من الملفات
            ar_trans = self.load_translation_file('ar')
            en_trans = self.load_translation_file('en')
            
            # تحديث البيانات الحالية
            self.current_data = {"ar": ar_trans, "en": en_trans}
            
            # مسح الجدول الحالي
            self.table.clearContents()
            self.table.setRowCount(0)
            
            # دمج المفاتيح من اللغتين
            all_keys = sorted(set(list(ar_trans.keys()) + list(en_trans.keys())))
            
            # تعبئة الجدول بالبيانات الجديدة
            self.table.setRowCount(len(all_keys))
            for row, key in enumerate(all_keys):
                # العمود 0: المفتاح
                key_item = QTableWidgetItem(key)
                key_item.setFlags(key_item.flags() | Qt.ItemIsEditable)
                self.table.setItem(row, 0, key_item)
                
                # العمود 1: النص العربي
                ar_item = QTableWidgetItem(ar_trans.get(key, ""))
                ar_item.setFlags(ar_item.flags() | Qt.ItemIsEditable)
                self.table.setItem(row, 1, ar_item)
                
                # العمود 2: النص الإنجليزي
                en_item = QTableWidgetItem(en_trans.get(key, ""))
                en_item.setFlags(en_item.flags() | Qt.ItemIsEditable)
                self.table.setItem(row, 2, en_item)
            
            # إعادة تطبيق أي تصفية كانت مفعلة
            self.filter_table(self.search_input.text())
            
            # تحديث الواجهة
            self.table.viewport().update()
            QTimer.singleShot(100, self.force_table_refresh)
            
            self.update_status(tr("static_texts_reloaded_successfully"))
            QMessageBox.information(self, tr("success"), tr("static_texts_reloaded_successfully"))
            logging.info("Static texts reloaded successfully")
        except Exception as e:
            error_msg = f"Error reloading static texts: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            QMessageBox.critical(self, tr("error"), error_msg)

    def force_table_refresh(self):
        """إجبار الجدول على التحديث"""
        self.table.viewport().update()
        self.table.update()
        self.table.repaint()
        QApplication.processEvents()

    def filter_table(self, text):
        text = text.lower()
        for row in range(self.table.rowCount()):
            key_item = self.table.item(row, 0)
            ar_item = self.table.item(row, 1)
            en_item = self.table.item(row, 2)
            match = False
            if key_item and text in key_item.text().lower():
                match = True
            elif ar_item and ar_item.text() and text in ar_item.text().lower():
                match = True
            elif en_item and en_item.text() and text in en_item.text().lower():
                match = True
            self.table.setRowHidden(row, not match)

    def filter_unused_keys(self):
        """إظهار المفاتيح غير المستخدمة فقط"""
        for row in range(self.table.rowCount()):
            key_item = self.table.item(row, 0)
            if key_item:
                # إذا كان المفتاح غير مستخدم، نظهر الصف. وإلا نخفيه.
                is_used = self.is_key_used(key_item.text())
                self.table.setRowHidden(row, is_used)

    def is_key_used(self, key):
        """التحقق من استخدام المفتاح في التطبيق (دالة مؤقتة)"""
        # TODO: تنفيذ آلية حقيقية للتحقق من استخدام المفتاح في الكود
        # حالياً: إرجاع False لجميع المفاتيح (تعتبر غير مستخدمة)
        return False

    def clear_filters(self):
        self.search_input.clear()
        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row, False)

    def show_context_menu(self, position):
        menu = QMenu()
        add_action = QAction(tr("add_key"), self)
        add_action.triggered.connect(self.add_new_key)
        menu.addAction(add_action)

        if self.table.selectedItems():
            delete_action = QAction(tr("delete_key"), self)
            delete_action.triggered.connect(self.delete_selected_key)
            menu.addAction(delete_action)

        copy_action = QAction(tr("copy_key"), self)
        copy_action.triggered.connect(self.copy_selected_key)
        menu.addAction(copy_action)

        menu.exec_(self.table.viewport().mapToGlobal(position))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.table.setColumnWidth(0, 120)
        if self.table.columnCount() > 2:
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)