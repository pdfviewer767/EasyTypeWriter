import re
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import ui.login_dialog as login_dialog


class LoginSecurityTests(unittest.TestCase):
    def test_initial_admin_password_meets_registration_policy(self):
        password = login_dialog.generate_initial_admin_password()
        self.assertGreaterEqual(len(password), 8)
        self.assertRegex(password, r"[A-Za-z]")
        self.assertRegex(password, r"\d")
        self.assertRegex(password, r"[!@#$%^&*(),.?\":{}|<>]")

    def test_expired_lock_is_cleared_and_legacy_lock_can_recover(self):
        user = {"locked": True, "locked_until": 1200, "failed_attempts": 5}
        self.assertFalse(login_dialog.is_account_locked(user, now=1200))
        self.assertFalse(user["locked"])
        self.assertEqual(user["failed_attempts"], 0)

        legacy_user = {"locked": True, "failed_attempts": 5}
        self.assertFalse(login_dialog.is_account_locked(legacy_user, now=1200))
        self.assertFalse(legacy_user["locked"])

    def test_active_lock_remains_until_expiry(self):
        user = {"locked": True, "locked_until": 1201, "failed_attempts": 5}
        self.assertTrue(login_dialog.is_account_locked(user, now=1200))

    def test_disabled_user_is_rejected_before_password_check(self):
        warnings = []
        window = SimpleNamespace(
            lockout_time=None,
            login_user_input=SimpleNamespace(text=lambda: "disabled-user"),
            login_pass_input=SimpleNamespace(text=lambda: "password"),
            load_users=lambda: [{"username": "disabled-user", "active": False}],
            verify_password=lambda *args: self.fail("Disabled user password was checked"),
        )
        message_box = SimpleNamespace(warning=lambda *args: warnings.append(args[1]))

        with patch.object(login_dialog, "QMessageBox", message_box):
            login_dialog.LoginDialog.handle_login(window)

        self.assertEqual(warnings, ["حساب معطل"])


if __name__ == "__main__":
    unittest.main()