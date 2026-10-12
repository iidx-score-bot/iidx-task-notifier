
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# app.pyを読み込むためのテスト用環境変数
os.environ.setdefault("LINE_CHANNEL_SECRET", "test_secret")
os.environ.setdefault("LINE_CHANNEL_ACCESS_TOKEN", "test_token")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SECRET_KEY", "test_key")
os.environ.setdefault("LINE_GROUP_ID", "test_group")

# テスト時は実際のSupabaseへ接続しない
with patch("supabase.create_client", return_value=MagicMock()):
    import app as bot


class JoinCommandTests(unittest.TestCase):

    def setUp(self):
        self.event = MagicMock()
        self.event.source.type = "group"
        self.event.source.group_id = "test_group"
        self.event.source.room_id = None
        self.event.source.user_id = "test_user"
        self.event.message.text = "!参加"
        self.event.reply_token = "test_reply_token"

    def run_command(self):
        with patch.object(bot, "reply_message") as reply:
            bot.handle_message(self.event)
            return reply.call_args.args[1]

    def test_new_player(self):
        with patch.object(bot, "get_player", return_value=None):
            with patch.object(bot, "register_player") as register:
                result = self.run_command()

        register.assert_called_once()
        self.assertIn("登録が完了", result)

    def test_existing_player(self):
        with patch.object(
            bot,
            "get_player",
            return_value={"id": 1},
        ):
            with patch.object(bot, "register_player") as register:
                result = self.run_command()

        register.assert_not_called()
        self.assertIn("すでに", result)

    def test_wrong_group(self):
        self.event.source.group_id = "other_group"

        with patch.object(bot, "register_player") as register:
            result = self.run_command()

        register.assert_not_called()
        self.assertIn("登録できません", result)

    def test_missing_user_id(self):
        self.event.source.user_id = None

        with patch.object(bot, "register_player") as register:
            result = self.run_command()

        register.assert_not_called()
        self.assertIn("取得できません", result)


if __name__ == "__main__":
    unittest.main()
