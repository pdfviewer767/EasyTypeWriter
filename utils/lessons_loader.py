# utils/lessons_loader.py
import os
import json
from .resource import user_data_path

def load_lessons(lang):
    lessons_file = user_data_path(os.path.join("data", f"lessons_{lang}.json"))
    if not os.path.exists(lessons_file):
        return {}
    with open(lessons_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {"غير مصنفة": data}
    elif isinstance(data, dict):
        return data
    return {}