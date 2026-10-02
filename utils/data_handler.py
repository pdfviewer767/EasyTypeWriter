import os
import json
from datetime import datetime
from PyQt5.QtCore import QLocale
from utils.resource import user_data_path

# ملف نتائج المستخدم
DATA_FILE = user_data_path("user_data.json")

# اللغات المدعومة
LANGUAGES = {
    "ar": "ar",
    "en": "en"
}

def load_data():
    """تحميل بيانات المستخدم السابقة (نتائج السرعة والدقة)."""
    if not os.path.exists(DATA_FILE):
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_session(wpm, accuracy, duration):
    """حفظ جلسة جديدة للسرعة والدقة."""
    sessions = load_data()
    session = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "wpm": wpm,
        "accuracy": accuracy,
        "duration": duration
    }
    sessions.append(session)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=4)

def clear_data():
    """مسح جميع بيانات الجلسات السابقة."""
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)

def get_translation(key, language=None):
    """ترجمة النصوص من ملف اللغة."""
    if language is None:
        language = QLocale.system().name()[:2]
    lang = LANGUAGES.get(language, "english")

    translation_path = user_data_path(os.path.join("data", "translations", f"{lang}.json"))
    if not os.path.exists(translation_path):
        return key  # fallback

    try:
        with open(translation_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get(key, key)
    except Exception:
        return key

def load_lessons(language="en"):
    """تحميل الدروس بناءً على اللغة المحددة."""
    # استخدم نفس منطق الملفات المعتمد في باقي المشروع
    filename = "lessons_ar.json" if language == "ar" else "lessons_en.json"
    lessons_path = user_data_path(os.path.join("data", filename))
    if not os.path.exists(lessons_path):
        return {}
    try:
        with open(lessons_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
