import os

EXCLUDED_DIRS = {'.venv', '__pycache__'}
OUTPUT_FILE = 'structure.txt'

def print_tree(startpath, file):
    for root, dirs, files in os.walk(startpath):
        # استبعاد المجلدات الغير مرغوبة
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        level = root.replace(startpath, '').count(os.sep)
        indent = '│   ' * level + '├── '
        file.write(f"{indent}{os.path.basename(root)}\n")

        subindent = '│   ' * (level + 1)
        for f in files:
            file.write(f"{subindent}├── {f}\n")

if __name__ == '__main__':
    base_path = os.getcwd()
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        print_tree(base_path, f)

    print(f"✅ Done! File saved as: {OUTPUT_FILE}")
