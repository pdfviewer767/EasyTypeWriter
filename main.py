import sys
import traceback
import os
import json
from PyQt5.QtWidgets import QApplication, QMessageBox
from core.settings_manager import SettingsManager
from ui.main_window import MainWindow
from ui.login_dialog import LoginDialog
from utils.translation_manager import TranslationManager
from utils.tr import tr, set_translation_manager

def resource_path(relative_path):
    """تُرجع المسار المطلق للملف المطلوب"""
    try:
        base_path = sys._MEIPASS  # عند التحزيم
    except Exception:
        base_path = os.path.abspath(".")  # عند التشغيل العادي
    return os.path.join(base_path, relative_path)

def load_stylesheet():
    """تحميل محتوى ملف التنسيق من مجلد style بجانب ملف main.py"""
    try:
        import pathlib
        base_dir = pathlib.Path(__file__).resolve().parent
        style_path = base_dir / "styles" / "app.qss"

        if style_path.exists():
            return style_path.read_text(encoding="utf-8")

        # إذا لم يعثر على الملف
        raise FileNotFoundError(f"لم يتم العثور على ملف التنسيق: {style_path}")
        
    except Exception as e:
        error_msg = f"خطأ في تحميل ملف التنسيق:\n{str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        return ""

def initialize_application():
    """تهيئة التطبيق الرئيسي وإعداد الإعدادات والترجمة"""
    try:
        
        # إنشاء مدير الإعدادات
        app = QApplication.instance() or QApplication(sys.argv)
        settings_manager = SettingsManager()
        
        # إعداد نظام الترجمة الجديد
        translation_manager = TranslationManager(app, settings_manager)
        translation_manager.load_translations()
        
        # تحميل وتطبيق ملف التنسيق الموحد
        stylesheet = load_stylesheet()
        if stylesheet:
            app.setStyleSheet(stylesheet)

        # --- التحقق من صلاحية الأدمن ---
        user_data = None

        # عرض مربع تسجيل الدخول
        login_dialog = LoginDialog(translation_manager)
        if login_dialog.exec_() == login_dialog.Accepted:
            # الحصول على بيانات المستخدم كاملة
            user_data = login_dialog.get_user_data()
            
            if not user_data:
                QMessageBox.critical(None, tr("error"), tr("user_data_not_found"))
                return 1
        else:
            sys.exit(0)

        # إنشاء النافذة الرئيسية مع صلاحية الأدمن وبيانات المستخدم
        main_window = MainWindow(
            app,  # تمرير تطبيق QApplication
            settings_manager,
            is_admin=user_data.get("is_admin", False),
            user_data=user_data  # تمرير بيانات المستخدم الكاملة
        )
        main_window.show()

        # بدء دورة حياة التطبيق
        return app.exec_()

    except Exception as e:
        # معالجة الأخطاء العامة
        error_msg = f"خطأ فادح في تهيئة التطبيق:\n{str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)

        # إنشاء تطبيق مؤقت لعرض رسالة الخطأ
        QMessageBox.critical(
            None,
            tr("application_error"),
            f"{tr('unexpected_error')}:\n\n{str(e)}\n\n{tr('check_logs')}"
        )
        return 1

if __name__ == "__main__":
    # تشغيل التطبيق وإدارة دورة الحياة
    exit_code = initialize_application()
    sys.exit(exit_code)