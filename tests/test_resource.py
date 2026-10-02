import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from utils.resource import migrate_user_images, user_data_directory, user_data_path


class UserDataPathTests(unittest.TestCase):
    def test_existing_resource_is_migrated_once_to_user_data(self):
        with tempfile.TemporaryDirectory() as directory:
            app_data = Path(directory) / "appdata"
            legacy_file = Path(directory) / "legacy-users.json"
            legacy_file.write_text('{"users": {}}', encoding="utf-8")
            with patch.dict(os.environ, {"APPDATA": str(app_data)}):
                with patch("utils.resource.resource_path", return_value=str(legacy_file)):
                    destination = Path(user_data_path("data/users.json"))
                    self.assertEqual(destination.read_text(encoding="utf-8"), '{"users": {}}')
                    legacy_file.write_text("updated", encoding="utf-8")
                    self.assertEqual(Path(user_data_path("data/users.json")), destination)
                    self.assertEqual(destination.read_text(encoding="utf-8"), '{"users": {}}')

            self.assertTrue(destination.is_relative_to(app_data))

    def test_profile_images_move_and_user_record_is_rewritten(self):
        with tempfile.TemporaryDirectory() as directory:
            app_data = Path(directory) / "appdata"
            old_image = Path(directory) / "old-image.jpg"
            old_image.write_bytes(b"image-bytes")
            users = [{"username": "alice", "image": str(old_image)}]

            with patch.dict(os.environ, {"APPDATA": str(app_data)}):
                self.assertTrue(migrate_user_images(users))
                migrated_image = Path(users[0]["image"])

            self.assertEqual(migrated_image.read_bytes(), b"image-bytes")
            self.assertTrue(migrated_image.is_relative_to(app_data))

    def test_legacy_application_data_is_migrated_without_overwriting(self):
        with tempfile.TemporaryDirectory() as directory:
            app_data = Path(directory) / "appdata"
            legacy_root = app_data / "AdamTyping"
            new_root = app_data / "EasyTypeWriter"
            legacy_root.mkdir(parents=True)
            (legacy_root / "settings.json").write_text("legacy", encoding="utf-8")
            (legacy_root / "data").mkdir()
            (legacy_root / "data" / "users.json").write_text("users", encoding="utf-8")
            new_root.mkdir()
            (new_root / "settings.json").write_text("current", encoding="utf-8")

            with patch.dict(os.environ, {"APPDATA": str(app_data)}):
                data_directory = Path(user_data_directory("data"))

            self.assertEqual((new_root / "settings.json").read_text(encoding="utf-8"), "current")
            self.assertEqual((data_directory / "users.json").read_text(encoding="utf-8"), "users")
            self.assertTrue(legacy_root.exists())


if __name__ == "__main__":
    unittest.main()