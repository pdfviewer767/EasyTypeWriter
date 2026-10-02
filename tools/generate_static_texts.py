# tools/generate_static_texts.py
# This script extracts static texts from the project files and generates translation keys.
import os
import re
import json
import time
from googletrans import Translator

PROJECT_PATH = r"D:\touch_typing_trainer"
TRANSLATIONS_DIR = os.path.join(PROJECT_PATH, "data")
OUTPUT_AR_FILE = os.path.join(TRANSLATIONS_DIR, "static_strings_ar.json")
OUTPUT_EN_FILE = os.path.join(TRANSLATIONS_DIR, "static_strings_en.json")

translator = Translator()

STRING_PATTERNS = [
    r'\.setText\(\s*"([^"]+)"\s*\)',
    r'\.setTitle\(\s*"([^"]+)"\s*\)',
    r'\.setWindowTitle\(\s*"([^"]+)"\s*\)',
    r'\.setToolTip\(\s*"([^"]+)"\s*\)',
    r'\.setWhatsThis\(\s*"([^"]+)"\s*\)',
    r'\.setPlaceholderText\(\s*"([^"]+)"\s*\)',
    r'\.setHtml\(\s*"([^"]+)"\s*\)',
    r'\.setShortcut\(\s*"([^"]+)"\s*\)',
    r'msgBox\.\w+\(\s*"([^"]+)"\s*\)',
    r'\bQMessageBox\.\w+\(\s*"([^"]+)"',
    r'\bQLabel\(\s*"([^"]+)"\s*\)',
    r'\bQPushButton\(\s*"([^"]+)"\s*\)',
    r'\bQCheckBox\(\s*"([^"]+)"\s*\)',
    r'\bQRadioButton\(\s*"([^"]+)"\s*\)',
    r'\bQGroupBox\(\s*"([^"]+)"\s*\)',
    r'\bQTabWidget\.addTab\([^)"]*,\s*"([^"]+)"\s*\)',
    r'\baddTab\(\w+,\s*"([^"]+)"\s*\)',
    r'\btr\(\s*"([^"]+)"\s*\)',
]

def remove_html_tags(text):
    return re.sub(r'<[^>]+>', '', text)

def clean_text(text):
    text = remove_html_tags(text)
    text = re.sub(r"\[.*?\]", "", text)
    text = text.replace("\\n", " ").replace("\n", " ")
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def is_readable(text):
    if not text or len(text.strip()) < 2:
        return False
    if re.search(r'\{.*?\}|%[sdf]|\\[nt]', text):
        return False
    if re.match(r'^\s+$', text):
        return False
    return True

def extract_strings_from_file(file_path):
    strings = set()
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        for pattern in STRING_PATTERNS:
            matches = re.findall(pattern, content)
            for match in matches:
                cleaned = clean_text(match)
                if is_readable(cleaned):
                    strings.add(cleaned)
    return strings

def walk_project_and_extract_strings(root_path):
    all_strings = set()
    for root, dirs, files in os.walk(root_path):
        for skip in ('venv', '.git', 'build', 'dist', '__pycache__'):
            if skip in dirs:
                dirs.remove(skip)
        for file in files:
            if file.endswith((".py", ".ui", ".qss")):
                full_path = os.path.join(root, file)
                extracted = extract_strings_from_file(full_path)
                all_strings.update(extracted)
    return sorted(all_strings)

def auto_translate_ar_to_en(ar_texts):
    en_translations = {}
    print("🔄 يتم الترجمة إلى الإنجليزية...")
    for i, text in enumerate(ar_texts):
        try:
            if i > 0 and i % 10 == 0:
                time.sleep(1)
            if re.search(r'[\u0600-\u06FF]', text):
                translated = translator.translate(text, src="ar", dest="en").text
                en_translations[text] = translated
                print(f"✓ تمت ترجمة: {text} → {translated}")
            else:
                en_translations[text] = text
                print(f"ℹ️ نص إنجليزي محفوظ: {text}")
        except Exception as e:
            print(f"⚠️ خطأ في ترجمة '{text}': {str(e)}")
            en_translations[text] = ""
    return en_translations

def save_translation_keys(ar_texts, en_translations, ar_path, en_path):
    ar_dict = {}
    en_dict = {}
    
    for text in ar_texts:
        ar_dict[text] = text
        en_dict[text] = en_translations.get(text, "")
    
    os.makedirs(os.path.dirname(ar_path), exist_ok=True)
    
    with open(ar_path, "w", encoding="utf-8") as f:
        json.dump(ar_dict, f, indent=2, ensure_ascii=False)
    
    with open(en_path, "w", encoding="utf-8") as f:
        json.dump(en_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ تم إنشاء {len(ar_dict)} نص للترجمة")
    print(f"📝 ملف العربية: {ar_path}")
    print(f"📝 ملف الإنجليزية: {en_path}")

def main():
    print("⏳ بدء استخراج النصوص من المشروع...")
    all_strings = walk_project_and_extract_strings(PROJECT_PATH)
    print(f"🔍 تم العثور على {len(all_strings)} نصًا")
    
    en_translations = auto_translate_ar_to_en(all_strings)
    
    save_translation_keys(all_strings, en_translations, OUTPUT_AR_FILE, OUTPUT_EN_FILE)

if __name__ == "__main__":
    main()
