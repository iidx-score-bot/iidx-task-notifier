```python
import os
import random
import logging

from supabase import create_client

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 環境変数
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_GROUP_ID = os.environ["LINE_GROUP_ID"]

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SECRET_KEY = os.environ["SUPABASE_SECRET_KEY"]


# クライアント初期化
supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY,
)

configuration = Configuration(
    access_token=LINE_CHANNEL_ACCESS_TOKEN
)


def get_random_songs():
    """☆5・☆6・☆7のSP譜面から各1曲を選ぶ。"""

    target_levels = [5, 6, 7]
    result_lines = ["【今週のIIDX課題曲】", ""]

    for level in target_levels:
        response = (
            supabase.table("charts")
            .select("*")
            .eq("play_style", "SP")
            .eq("level", level)
            .eq("is_ac_active", True)
            .execute()
        )

        charts = response.data

        if not charts:
            raise RuntimeError(
                f"☆{level}の対象譜面が見つかりません"
            )

        chart = random.choice(charts)
        song_id = chart.get("song_id")

        if not song_id:
            raise RuntimeError(
                f"☆{level}の譜面にsong_idがありません"
            )

        song_response = (
            supabase.table("songs")
            .select("id, title")
            .eq("id", song_id)
            .limit(1)
            .execute()
        )

        songs = song_response.data

        if not songs:
            raise RuntimeError(
                f"☆{level}の楽曲情報が見つかりません"
            )

        title = songs[0].get("title", "曲名不明")

        result_lines.append(f"☆{level}：{title}")

    result_lines.extend([
        "",
        "プレイしたらスコアを共有しよう！",
    ])

    return "\n".join(result_lines)


def main():
    message = get_random_songs()

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        line_bot_api.push_message(
            PushMessageRequest(
                to=LINE_GROUP_ID,
                messages=[
                    TextMessage(text=message)
                ],
            )
        )

    logger.info("週次課題曲をLINEグループに投稿しました")


if __name__ == "__main__":
    main()
```
