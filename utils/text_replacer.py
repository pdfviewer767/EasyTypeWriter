import os
import re
import json
import shutil
from pathlib import Path
from utils.resource import resource_path


def replace_texts_with_keys(project_path):
    """استبدال النصوص في المشروع بمفاتيح الترجمة"""
    # مسارات الملفات
    static_path = os.path.join(project_path, "data", "static_strings.json")
    translations_dir = os.path.join(project_path, "data", "translations")
    backup_dir = os.path.join(project_path, "backup")
    
    # إنشاء نسخة احتياطية
    os.makedirs(backup_dir, exist_ok=True)
    shutil.copytree(project_path, os.path.join(backup_dir, "pre_translate"), dirs_exist_ok=True)
    
    # تحميل بيانات الترجمات
    with open(static_path, "r", encoding="utf-8") as f:
        static_data = json.load(f)
    
    # إنشاء قاموس للبحث العكسي (النص -> المفتاح)
    reverse_dict = {}
    for key, value in static_data["ar"].items():
        if value:  # تجاهل القيم الفارغة
            reverse_dict[value] = key
    
    # مسح المشروع واستبدال النصوص
    for root, dirs, files in os.walk(project_path):
        # تجاهل بعض المجلدات
        if "backup" in dirs:
            dirs.remove("backup")
        if "data" in dirs:
            dirs.remove("data")
        if "venv" in dirs:
            dirs.remove("venv")
        if ".git" in dirs:
            dirs.remove(".git")
        
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                
                # قراءة المحتوى
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # استبدال النصوص بالمفاتيح
                new_content = content
                for text, key in reverse_dict.items():
                    # تجنب استبدال النصوص داخل التعليقات
                    pattern = r'([^\'"#])' + re.escape(text)
                    replacement = r'\1tr("' + key + '")'
                    new_content = re.sub(pattern, replacement, new_content)
                
                # حفظ التغييرات
                if new_content != content:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
    
    return f"✅ تم استبدال {len(reverse_dict)} نصاً بمفاتيح الترجمة\n⚠️ تم إنشاء نسخة احتياطية في: {backup_dir}"