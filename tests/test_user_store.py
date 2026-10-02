import unittest

from ui.admin_panel.stats_screen import normalize_user_records


class UserStoreTests(unittest.TestCase):
    def test_wrapped_user_store_is_normalized(self):
        records = normalize_user_records(
            {"users": {"alice": {"active": True}, "bob": {"active": False}}}
        )
        self.assertEqual(
            records,
            [
                {"active": True, "username": "alice"},
                {"active": False, "username": "bob"},
            ],
        )

    def test_legacy_user_list_is_supported(self):
        records = normalize_user_records(
            [{"username": "alice", "active": True}, "bob", None]
        )
        self.assertEqual(
            records,
            [{"username": "alice", "active": True}, {"username": "bob"}],
        )


if __name__ == "__main__":
    unittest.main()