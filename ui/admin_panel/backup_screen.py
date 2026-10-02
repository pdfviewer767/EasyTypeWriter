# backup_screen.py
# شاشة النسخ الاحتياطي واستيراد/تصدير البيانات في التطبيق
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox
import os
import json
import shutil
import stat
import zipfile
from pathlib import PurePosixPath
from utils.tr import tr
from utils.translation_manager import TranslationManager
from utils.resource import user_data_directory, user_data_path

MAX_BACKUP_SIZE = 256 * 1024 * 1024


def create_app_data_backup(archive_path, data_root):
    archive_path = os.path.abspath(archive_path)
    data_root = os.path.abspath(data_root)
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for root, _, files in os.walk(data_root):
            for filename in files:
                file_path = os.path.join(root, filename)
                if os.path.abspath(file_path) == archive_path:
                    continue
                archive_name = os.path.relpath(file_path, data_root)
                if archive_name.lower() == "encryption.key":
                    continue
                archive.write(file_path, archive_name.replace(os.sep, "/"))


def restore_app_data_backup(archive_path, data_root):
    data_root = os.path.abspath(data_root)
    pending_entries = []
    seen_paths = set()
    total_size = 0

    with zipfile.ZipFile(archive_path, "r") as archive:
        for entry in archive.infolist():
            member_name = entry.filename.replace("\\", "/")
            member_path = PurePosixPath(member_name)
            if member_path.is_absolute() or ".." in member_path.parts or not member_path.parts:
                raise ValueError("ملف النسخة الاحتياطية يحتوي على مسار غير آمن")
            if member_path.parts[0] not in {"data", "settings.json"}:
                raise ValueError("ملف النسخة الاحتياطية يحتوي على ملف غير مدعوم")
            if member_path.parts[0] == "settings.json" and len(member_path.parts) != 1:
                raise ValueError("مسار الإعدادات غير صالح")
            if os.name == "nt" and any(":" in part for part in member_path.parts):
                raise ValueError("ملف النسخة الاحتياطية يحتوي على مسار غير آمن")
            if stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError("لا يمكن استعادة روابط رمزية من النسخة الاحتياطية")

            destination = os.path.abspath(os.path.join(data_root, *member_path.parts))
            if os.path.commonpath([data_root, destination]) != data_root:
                raise ValueError("ملف النسخة الاحتياطية يحتوي على مسار غير آمن")
            normalized_destination = os.path.normcase(destination)
            if normalized_destination in seen_paths:
                raise ValueError("ملف النسخة الاحتياطية يحتوي على مسارات مكررة")
            seen_paths.add(normalized_destination)

            total_size += entry.file_size
            if total_size > MAX_BACKUP_SIZE:
                raise ValueError("حجم النسخة الاحتياطية يتجاوز الحد المسموح")
            pending_entries.append((entry, destination))

        for entry, destination in pending_entries:
            if entry.is_dir():
                os.makedirs(destination, exist_ok=True)
                continue

            os.makedirs(os.path.dirname(destination), exist_ok=True)
            temporary_path = destination + ".restore.tmp"
            try:
                with archive.open(entry, "r") as source, open(temporary_path, "wb") as target:
                    shutil.copyfileobj(source, target)
                os.replace(temporary_path, destination)
            finally:
                if os.path.exists(temporary_path):
                    os.remove(temporary_path)


class BackupScreen(QWidget):
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

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("🗄️ النسخ الاحتياطي واستيراد/تصدير البيانات"))

        backup_btn = QPushButton("🔄 نسخ احتياطي للبيانات")
        restore_btn = QPushButton("⏪ استرجاع نسخة احتياطية")
        export_btn = QPushButton("📤 تصدير البيانات")
        import_btn = QPushButton("📥 استيراد البيانات")

        for btn in [backup_btn, restore_btn, export_btn, import_btn]:
            btn.setStyleSheet(self.btn_style())
            layout.addWidget(btn)

        backup_btn.clicked.connect(self.backup_data)
        restore_btn.clicked.connect(self.restore_data)
        export_btn.clicked.connect(self.export_data)
        import_btn.clicked.connect(self.import_data)

    def btn_style(self):
        return """
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

    def backup_data(self):
        path, _ = QFileDialog.getSaveFileName(self, "اختر مكان حفظ النسخة الاحتياطية", "backup.zip", "Zip Files (*.zip)")
        if path:
            try:
                data_root = user_data_directory()
                create_app_data_backup(path, data_root)
                QMessageBox.information(self, "تم النسخ الاحتياطي", f"تم حفظ النسخة الاحتياطية في:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل النسخ الاحتياطي:\n{str(e)}")

    def restore_data(self):
        path, _ = QFileDialog.getOpenFileName(self, "اختر ملف النسخة الاحتياطية", "", "Zip Files (*.zip)")
        if path:
            try:
                restore_app_data_backup(path, user_data_directory())
                QMessageBox.information(self, "تم الاسترجاع", f"تم استرجاع البيانات من:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل الاسترجاع:\n{str(e)}")

    def export_data(self):
        path, _ = QFileDialog.getSaveFileName(self, "اختر مكان تصدير البيانات", "export.json", "JSON Files (*.json)")
        if path:
            try:
                data_dir = user_data_path(os.path.join("data", "users.json"))
                shutil.copyfile(data_dir, path)
                QMessageBox.information(self, "تم التصدير", f"تم تصدير البيانات إلى:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل التصدير:\n{str(e)}")

    def import_data(self):
        path, _ = QFileDialog.getOpenFileName(self, "اختر ملف البيانات للاستيراد", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as source:
                    imported = json.load(source)
                if isinstance(imported, list):
                    users = imported
                elif isinstance(imported, dict):
                    users = imported.get("users", {})
                    users = list(users.values()) if isinstance(users, dict) else users
                else:
                    raise ValueError("تنسيق ملف المستخدمين غير صالح")
                if not isinstance(users, list) or not all(isinstance(user, dict) and user.get("username") for user in users):
                    raise ValueError("بيانات المستخدمين غير صالحة")
                data_dir = user_data_path(os.path.join("data", "users.json"))
                with open(data_dir, "w", encoding="utf-8") as target:
                    json.dump(
                        {"users": {user["username"]: user for user in users}},
                        target,
                        ensure_ascii=False,
                        indent=2,
                    )
                QMessageBox.information(self, "تم الاستيراد", f"تم استيراد البيانات من:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل الاستيراد:\n{str(e)}")
