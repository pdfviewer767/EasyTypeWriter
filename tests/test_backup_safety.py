import tempfile
import unittest
import zipfile
from pathlib import Path

from ui.admin_panel.backup_screen import create_app_data_backup, restore_app_data_backup


class BackupSafetyTests(unittest.TestCase):
    def test_backup_contains_app_data_but_not_encryption_key(self):
        with tempfile.TemporaryDirectory() as directory:
            data_root = Path(directory) / "app-data"
            (data_root / "data").mkdir(parents=True)
            (data_root / "data" / "users.json").write_text("{}", encoding="utf-8")
            (data_root / "encryption.key").write_text("secret", encoding="utf-8")
            archive_path = Path(directory) / "backup.zip"

            create_app_data_backup(str(archive_path), str(data_root))

            with zipfile.ZipFile(archive_path) as archive:
                self.assertEqual(archive.namelist(), ["data/users.json"])

    def test_restore_validates_every_entry_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "unsafe.zip"
            data_root = Path(directory) / "restored"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("data/valid.json", "{}")
                archive.writestr("../outside.json", "unsafe")

            with self.assertRaises(ValueError):
                restore_app_data_backup(str(archive_path), str(data_root))

            self.assertFalse((data_root / "data" / "valid.json").exists())
            self.assertFalse((Path(directory) / "outside.json").exists())


if __name__ == "__main__":
    unittest.main()