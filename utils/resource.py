import sys
import os
import shutil

APP_DATA_NAME = "EasyTypeWriter"
LEGACY_APP_DATA_NAME = "AdamTyping"

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""


    # Handle path separators for different OS
    relative_path = relative_path.replace('/', os.sep).replace('\\', os.sep)

    # 1. Try _MEIPASS (PyInstaller temp folder)
    base_path = getattr(sys, '_MEIPASS', None)
    if base_path:
        path = os.path.join(base_path, relative_path)
        if os.path.exists(path):
            return path

    # 2. Try next to executable (dist folder)
    exe_dir = os.path.dirname(getattr(sys, 'executable', ''))
    path = os.path.join(exe_dir, relative_path)
    if os.path.exists(path):
        return path

    # 2.5. Try _internal/data next to exe (for PyInstaller)
    internal_data_dir = os.path.join(exe_dir, '_internal', 'data')
    internal_path = os.path.join(internal_data_dir, relative_path)
    if os.path.exists(internal_path):
        return internal_path

    # 3. Try current working directory
    path = os.path.abspath(relative_path)
    if os.path.exists(path):
        return path

    # 4. Fallback: original PyInstaller logic
    if base_path:
        return os.path.join(base_path, relative_path)
    return os.path.abspath(relative_path)


def user_data_directory(*parts):
    """Return the writable per-user application data directory."""
    if os.name == "nt":
        base_path = os.environ.get("APPDATA") or os.path.join(
            os.path.expanduser("~"), "AppData", "Roaming"
        )
    elif sys.platform == "darwin":
        base_path = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base_path = os.environ.get(
            "XDG_DATA_HOME", os.path.join(os.path.expanduser("~"), ".local", "share")
        )

    app_data_root = os.path.join(base_path, APP_DATA_NAME)
    legacy_data_root = os.path.join(base_path, LEGACY_APP_DATA_NAME)
    if os.path.isdir(legacy_data_root):
        os.makedirs(app_data_root, exist_ok=True)
        shutil.copytree(
            legacy_data_root,
            app_data_root,
            dirs_exist_ok=True,
            copy_function=_copy_file_if_missing,
        )

    directory = os.path.join(app_data_root, *parts)
    os.makedirs(directory, exist_ok=True)
    return directory


def _copy_file_if_missing(source, destination):
    if os.path.exists(destination):
        return destination
    return shutil.copy2(source, destination)


def user_data_path(relative_path):
    """Return a writable user-data path, migrating an existing bundled file once."""
    relative_path = relative_path.replace("/", os.sep).replace("\\", os.sep)
    normalized_path = os.path.normpath(relative_path)
    if os.path.isabs(normalized_path) or normalized_path == os.pardir or normalized_path.startswith(
        os.pardir + os.sep
    ):
        raise ValueError("User data paths must stay inside the application data directory")

    destination = os.path.join(user_data_directory(), normalized_path)
    os.makedirs(os.path.dirname(destination), exist_ok=True)

    if not os.path.exists(destination):
        source = resource_path(relative_path)
        if os.path.isfile(source) and os.path.abspath(source) != os.path.abspath(destination):
            shutil.copy2(source, destination)

    return destination


def migrate_user_images(users):
    image_directory = user_data_directory("data", "user_images")
    changed = False

    for user in users:
        image_path = user.get("image", "")
        if not image_path:
            continue

        source = image_path if os.path.isfile(image_path) else resource_path(image_path)
        if not os.path.isfile(source):
            continue

        destination = os.path.join(image_directory, os.path.basename(source))
        if os.path.normcase(os.path.abspath(source)) != os.path.normcase(os.path.abspath(destination)):
            if not os.path.exists(destination):
                shutil.copy2(source, destination)
            user["image"] = destination
            changed = True

    return changed


