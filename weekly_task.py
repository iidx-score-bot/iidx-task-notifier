import os
import random
import sys

from supabase import create_client
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage,
)

def main():
    # 環境変数
    supabase_url = os.environ["SUPABASE_URL"]
    supabase_key = os.environ["SUPABASE_SECRET_KEY"]
    line_access_token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
    group_id = os.environ["LINE_GROUP_ID"]

    # Supabase接続
    supabase = create_client(supabase_url, supabase_key)

    # 楽曲・譜面データを取得
    message_lines = ["🎹 今週の弐寺課題曲！", ""]

    for level in [5, 6, 7]:
        response = (
            supabase.table("charts")
            .select("id,song_id,play_style,difficulty,level")
            .eq("play_style", "SP")
            .eq("level", level)
            .eq("is_ac_active", True)
            .execute()
        )

        charts = response.data

        if not charts:
            raise RuntimeError(f"SP☆{level}の対象譜面がありません")

        chart = random.choice(charts)

        song_response = (
            supabase.table("songs")
            .select("*")
            .eq("id", chart["song_id"])
            .limit(1)
            .execute()
        )

        if not song_response.data:
            raise RuntimeError(
                f"譜面ID {chart['id']} に対応する楽曲がありません"
            )

        song = song_response.data[0]

        # songsテーブルの楽曲名カラムを取得
        song_name = (
            song.get("title")
            or song.get("name")
            or song.get("song_name")
        )

        if not song_name:
            raise RuntimeError(
                "songsテーブルの楽曲名カラムを確認してください"
            )

        message_lines.append(f"【SP☆{level}】")
        message_lines.append(f"曲名：{song_name}")
        message_lines.append(f"譜面：{chart['difficulty']}")
        message_lines.append("")

    message_lines.append("今週も頑張りましょう！")
    message_text = "\n".join(message_lines)

    # LINEグループへPush送信
    configuration = Configuration(
        access_token=line_access_token
    )

    with ApiClient(configuration) as api_client:
        line_api = MessagingApi(api_client)
        line_api.push_message(
            PushMessageRequest(
                to=group_id,
                messages=[TextMessage(text=message_text)],
            )
        )

    print("週次課題曲の通知が完了しました")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"週次通知エラー: {exc}", file=sys.stderr)
        raise
