import json
import os
from PyQt5.QtCore import QCoreApplication
from utils.resource import user_data_path

class TranslationManager:
    def __init__(self, app, settings_manager):
        self.app = app
        self.settings_manager = settings_manager  # هذا السطر ضروري
        self.translations = {}
        self.current_lang = None
        
    def load_translations(self):
        """تحميل الترجمات من ملفات JSON"""
        try:
            lang = self.settings_manager.get_language()
            self.current_lang = lang
            
            # تحديد مسار ملف الترجمة الصحيح
            translation_file = user_data_path(os.path.join("data", "translations", f"{lang}.json"))
            if not os.path.exists(translation_file):
                # إذا لم يوجد ملف للغة المحددة، استخدم اللغة الإنجليزية كافتراضي
                translation_file = user_data_path(os.path.join("data", "translations", "en.json"))
                # إذا لم يوجد ملف إنجليزي، استخدم ترجمة افتراضية فارغة
                if not os.path.exists(translation_file):
                    self.translations = {}
                    return
            # تحميل ملف الترجمة
            with open(translation_file, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
                
        except Exception as e:
            print(f"خطأ في تحميل الترجمات: {str(e)}")
            self.translations = {}
    
    def translate(self, key):
        """ترجمة مفتاح معين"""
        return self.translations.get(key, key)
    
    def get_language(self):
        """الحصول على اللغة الحالية"""
        try:
            # التأكد من وجود settings_manager قبل استخدامه
            if hasattr(self, 'settings_manager') and self.settings_manager:
                return self.settings_manager.get_language()
        except Exception as e:
            print(f"خطأ في الحصول على اللغة: {str(e)}")
        
        # إرجاع لغة افتراضية في حالة الخطأ
        return "ar"
    
    # يمكنك إضافة المزيد من الدوال حسب الحاجة