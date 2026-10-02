import json
import os
from utils.resource import user_data_path

class SettingsManager:
    def __init__(self):
        self.settings_file = user_data_path("settings.json")
        self.settings = self.load_settings()
    
    def load_settings(self):
        """تحميل الإعدادات من ملف"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"خطأ في تحميل الإعدادات: {e}")
        return {}
    
    def save_settings(self):
        """حفظ الإعدادات إلى ملف"""
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"خطأ في حفظ الإعدادات: {e}")
            return False
    
    def get(self, key, default=None):
        """الحصول على قيمة إعداد"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """تعيين قيمة إعداد"""
        self.settings[key] = value