# data/lesson_loader.py

import json
import os
from utils.resource import user_data_path

def load_lessons(lang="ar"):
    filename = "lessons_ar.json" if lang == "ar" else "lessons_en.json"
    lessons_path = user_data_path(os.path.join("data", filename))
    with open(lessons_path, "r", encoding="utf-8") as f:
        return json.load(f)
