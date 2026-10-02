import json
import os
import tempfile
from .resource import user_data_path

def get_progress_file(username):
    return user_data_path(os.path.join("data", f"user_progress_{username}.json"))

def load_user_progress(username):
    file = get_progress_file(username)
    default_progress = {
        "completed_lessons_ar": [],
        "completed_lessons_en": [],
        "completed_training_levels": [],
        "completed_tests": [],
        "sessions_ar": [],
        "sessions_en": [],
        "practice_sessions": [],
        "completed_practice": {}
    }
    if not os.path.exists(file):
        return default_progress.copy()
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return default_progress.copy()
    if not isinstance(data, dict):
        return default_progress.copy()
    progress = {k: data.get(k, v) for k, v in default_progress.items()}
    return progress

def save_user_progress(username, progress, session=None, lang=None, practice_session=None, completed_practice=None):
    file = get_progress_file(username)
    data_dir = os.path.dirname(file)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            data = progress.copy()
        if not isinstance(data, dict):
            data = progress.copy()
    else:
        data = progress.copy()
    
    if session and lang:
        key = f"sessions_{lang}"
        if key not in data:
            data[key] = []
        data[key].append(session)
    
    if practice_session:
        if "practice_sessions" not in data:
            data["practice_sessions"] = []
        data["practice_sessions"].append(practice_session)
    
    for k, v in progress.items():
        if k.startswith("sessions_") or k == "practice_sessions":
            continue
        data[k] = v

    if completed_practice:
        if isinstance(completed_practice, dict):
            completed_by_language = completed_practice
        elif lang:
            completed_by_language = {lang: [completed_practice]}
        else:
            completed_by_language = {}

        saved_practice = data.get("completed_practice", {})
        if isinstance(saved_practice, list):
            saved_practice = {lang: saved_practice} if lang else {}
        if not isinstance(saved_practice, dict):
            saved_practice = {}

        for language, completed_items in completed_by_language.items():
            if not isinstance(completed_items, (list, tuple, set)):
                completed_items = [completed_items]
            language_items = saved_practice.setdefault(language, [])
            if not isinstance(language_items, list):
                language_items = saved_practice[language] = []
            for item in completed_items:
                if item not in language_items:
                    language_items.append(item)
        data["completed_practice"] = saved_practice
    
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=data_dir, delete=False
        ) as temporary_file:
            temporary_path = temporary_file.name
            json.dump(data, temporary_file, ensure_ascii=False, indent=2)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, file)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.remove(temporary_path)