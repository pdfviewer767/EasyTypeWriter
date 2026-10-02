# utils/resource.py
# This module provides a utility function to get the absolute path of resources in the application.
import sys
import os
from utils.resource import resource_path

def resource_path(relative_path):
    try:
        # بيئة التشغيل داخل PyInstaller
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
