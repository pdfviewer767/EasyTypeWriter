import os
import shutil
import subprocess
import sys
import json
import logging
import traceback

# إعداد نظام التسجيل
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('build_script.log'),
        logging.StreamHandler()
    ]
)

def prepare_translation_files():
    """تحضير ملفات الترجمة للتحزيم"""
    # إنشاء مجلد الترجمات إذا لم يكن موجوداً
    os.makedirs(os.path.join('data', 'translations'), exist_ok=True)
    
    for lang in ['ar', 'en']:
        src_path = os.path.join('data', 'translations', f'{lang}.json')
        
        # فقط إنشاء الملفات إذا لم تكن موجودة
        if not os.path.exists(src_path):
            try:
                # إنشاء ملف ترجمة فارغ
                with open(src_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)
                logging.info(f"Created empty translation file: {src_path}")
                print(f"Created empty translation file: {src_path}")
            except Exception as e:
                logging.error(f"Error creating translation file: {e}")
                print(f"Error creating translation file: {e}")

def main():
    logging.info("Starting build process")
    print("Starting build process")
    
    # حذف التحزيمات القديمة
    build_paths = [
        "build",
        "dist/EasyTypeWriter",
        "EasyTypeWriter.spec",
        "dist/Adam Typing",
        "Adam Typing.spec"
    ]
    
    old_build_exists = any(os.path.exists(path) for path in build_paths)
    
    if old_build_exists:
        print("Found old build files:")
        for path in build_paths:
            if os.path.exists(path):
                print(f" - {path}")
        
        response = input("Delete old build files? (y/n): ").strip().lower()
        
        if response == 'y':
            for path in build_paths:
                if os.path.exists(path):
                    if os.path.isfile(path):
                        os.remove(path)
                        print(f"Deleted file: {path}")
                        logging.info(f"Deleted file: {path}")
                    else:
                        shutil.rmtree(path)
                        print(f"Deleted directory: {path}")
                        logging.info(f"Deleted directory: {path}")
            print("Old build files deleted successfully!")
            logging.info("Old build files deleted successfully")
        else:
            print("Skipped deletion of old build files")
            logging.info("Skipped deletion of old build files")
    
    # تحضير ملفات الترجمة (إنشاءها إذا لم تكن موجودة)
    print("\nPreparing translation files...")
    logging.info("Preparing translation files")
    prepare_translation_files()
    
    # تشغيل أمر pyinstaller
    print("\nStarting packaging process...")
    logging.info("Running PyInstaller")
    
    # بناء أمر التحزيم
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "build.spec",
    ]
    
    try:
        logging.info(f"Running command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        print("\nPackaging completed successfully! You can find the application in the dist folder")
        logging.info("Build completed successfully")
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Packaging error: {e}"
        print(f"\n{error_msg}")
        logging.error(error_msg)
        print("Make sure PyInstaller is installed: pip install pyinstaller")
        sys.exit(1)
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(f"\n{error_msg}")
        logging.error(error_msg)
        logging.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()