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

    # 現行アーケード版で有効な楽曲を取得
    songs_response = (
        supabase.table("songs")
        .select("id,title,is_ac_active")
        .eq("is_ac_active", True)
        .execute()
    )

    active_songs = {
        song["id"]: song
        for song in songs_response.data
    }

    if not active_songs:
        raise RuntimeError("有効な楽曲が見つかりません")

    # 現行アーケード版で有効なSP譜面を取得
    charts_response = (
        supabase.table("charts")
        .select("id,song_id,play_style,difficulty,level,is_ac_active")
        .eq("play_style", "SP")
        .eq("is_ac_active", True)
        .in_("level", [5, 6, 7])
        .execute()
    )

    # 有効な楽曲に属する譜面だけを残す
    charts_by_level = {5: [], 6: [], 7: []}

    for chart in charts_response.data:
        if chart["song_id"] not in active_songs:
            continue

        charts_by_level[chart["level"]].append(chart)

    # 各レベルからランダムに1譜面選ぶ
    message_lines = ["🎹 今週の弐寺課題曲！", ""]

    for level in [5, 6, 7]:
        charts = charts_by_level[level]

        if not charts:
            raise RuntimeError(
                f"SP☆{level}の対象譜面がありません"
            )

        chart = random.choice(charts)
        song = active_songs[chart["song_id"]]

        message_lines.append(f"【SP☆{level}】")
        message_lines.append(f"曲名：{song['title']}")
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
        print(
            f"週次通知エラー: {exc}",
            file=sys.stderr,
        )
        raise
