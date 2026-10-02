# settings_manager.py
# This module manages application settings, including language, theme, and translations.
import json
import os
from utils.resource import user_data_path

class SettingsManager:
    def __init__(self, settings_file="settings.json"):
        self.settings_file = user_data_path(settings_file)
        self.settings = self.load_settings()

    def load_settings(self):
        if not os.path.exists(self.settings_file):
            return self.create_default_settings()

        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.create_default_settings()

    def create_default_settings(self):
        return {
            "language": "ar",
            "font_size": 16,
            "theme": "light",
            "translations": {}  # إضافة هذا الحقل الافتراضي
        }

    def save_settings(self):
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def get_language(self):
        return self.settings.get("language", "ar")

    def set_language(self, lang):
        self.settings["language"] = lang
        self.save_settings()

    # إضافة الدوال الجديدة
    def get_translations(self):
        return self.settings.get("translations", {})

    def set_translations(self, translations):
        self.settings["translations"] = translations
        self.save_settings()