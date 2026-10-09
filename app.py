import os
import random
import logging

from flask import Flask, request, abort
from supabase import create_client

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)

from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
)


# ==================================================
# 基本設定
# ==================================================

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================================================
# 環境変数
# Renderの Environment に設定する
# ==================================================

LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get(
    "LINE_CHANNEL_ACCESS_TOKEN"
)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.environ.get("SUPABASE_SECRET_KEY")


# ==================================================
# LINE / Supabase クライアント
# ==================================================

if not LINE_CHANNEL_SECRET:
    raise RuntimeError("LINE_CHANNEL_SECRET が設定されていません")

if not LINE_CHANNEL_ACCESS_TOKEN:
    raise RuntimeError(
        "LINE_CHANNEL_ACCESS_TOKEN が設定されていません"
    )

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL が設定されていません")

if not SUPABASE_SECRET_KEY:
    raise RuntimeError("SUPABASE_SECRET_KEY が設定されていません")


handler = WebhookHandler(LINE_CHANNEL_SECRET)

configuration = Configuration(
    access_token=LINE_CHANNEL_ACCESS_TOKEN
)

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY,
)


# ==================================================
# ホーム画面
# ==================================================

@app.route("/", methods=["GET"])
def home():
    return "IIDX Task Bot is running!"


# ==================================================
# LINE Webhook
# ==================================================

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    logger.info("LINE webhook received")

    try:
        handler.handle(body, signature)

    except InvalidSignatureError:
        logger.exception("LINE signature validation failed")
        abort(400)

    except Exception:
        logger.exception("LINE webhook processing failed")
        abort(500)

    return "OK"


# ==================================================
# LINEへの返信
# ==================================================

def reply_message(reply_token, text):
    """
    LINEにテキストメッセージを返信する。
    """

    if not reply_token:
        logger.warning("reply_token がありません")
        return

    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)

            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[
                        TextMessage(text=text)
                    ],
                )
            )

        logger.info("LINE reply sent")

    except Exception:
        logger.exception("LINE reply failed")
        raise


# ==================================================
# 最新の課題曲を取得
# ==================================================

def get_task_song(group_id):
    """
    指定されたグループの最新課題曲を取得する。

    前提テーブル:
      tasks
      charts
      songs

    tasks に group_id、chart_id、task_date が存在する想定。
    charts に id、song_id、play_style、level が存在する想定。
    songs に id、title が存在する想定。
    """

    if not group_id:
        return "グループIDを取得できませんでした。"

    # グループの最新課題曲を取得
    task_response = (
        supabase.table("tasks")
        .select("chart_id, task_date, group_id")
        .eq("group_id", group_id)
        .order("task_date", desc=True)
        .limit(1)
        .execute()
    )

    tasks = task_response.data

    if not tasks:
        return (
            "このグループにはまだ課題曲が登録されていません。\n"
            "課題曲の登録機能は今後追加できます。"
        )

    task = tasks[0]
    chart_id = task.get("chart_id")

    if not chart_id:
        return "課題曲の譜面IDが登録されていません。"

    # 譜面情報を取得
    chart_response = (
        supabase.table("charts")
        .select("*")
        .eq("id", chart_id)
        .limit(1)
        .execute()
    )

    charts = chart_response.data

    if not charts:
        return "課題曲の譜面情報が見つかりませんでした。"

    chart = charts[0]
    song_id = chart.get("song_id")

    if not song_id:
        return "譜面に対応する楽曲IDが見つかりませんでした。"

    # 楽曲情報を取得
    song_response = (
        supabase.table("songs")
        .select("*")
        .eq("id", song_id)
        .limit(1)
        .execute()
    )

    songs = song_response.data

    if not songs:
        return "課題曲の楽曲情報が見つかりませんでした。"

    song = songs[0]

    title = song.get("title", "曲名不明")
    play_style = chart.get("play_style", "SP")
    level = chart.get("level", "不明")
    task_date = task.get("task_date", "日付不明")

    return (
        "【現在の課題曲】\n"
        f"曲名：{title}\n"
        f"譜面：{play_style} ☆{level}\n"
        f"登録日：{task_date}"
    )


# ==================================================
# ランダム課題曲を取得
# ==================================================

def get_random_song():
    """
    ☆5・☆6・☆7のSP譜面からランダムに1曲ずつ選ぶ。

    前提:
      charts に song_id、play_style、level、is_ac_active が存在する。
      songs に id、title が存在する。
    """

    target_levels = [5, 6, 7]
    result_lines = ["【ランダム課題曲】"]

    for level in target_levels:
        try:
            chart_response = (
                supabase.table("charts")
                .select("*")
                .eq("play_style", "SP")
                .eq("level", level)
                .eq("is_ac_active", True)
                .execute()
            )

            charts = chart_response.data

            if not charts:
                result_lines.append(
                    f"☆{level}：対象譜面が見つかりませんでした。"
                )
                continue

            chart = random.choice(charts)
            song_id = chart.get("song_id")

            if not song_id:
                result_lines.append(
                    f"☆{level}：楽曲IDが設定されていません。"
                )
                continue

            song_response = (
                supabase.table("songs")
                .select("*")
                .eq("id", song_id)
                .limit(1)
                .execute()
            )

            songs = song_response.data

            if not songs:
                result_lines.append(
                    f"☆{level}：楽曲情報が見つかりませんでした。"
                )
                continue

            song = songs[0]
            title = song.get("title", "曲名不明")

            result_lines.append(
                f"☆{level}：{title}"
            )

        except Exception:
            logger.exception(
                "ランダム課題曲の取得に失敗しました: level=%s",
                level,
            )

            result_lines.append(
                f"☆{level}：取得中にエラーが発生しました。"
            )

    return "\n".join(result_lines)


# ==================================================
# LINEメッセージ処理
# ※ handle_message は1回だけ定義する
# ==================================================

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """
    LINEのテキストメッセージを受信してコマンドを処理する。
    """

    source = event.source
    source_type = getattr(source, "type", "unknown")

    group_id = getattr(source, "group_id", None)
    room_id = getattr(source, "room_id", None)
    user_id = getattr(source, "user_id", None)

    # グループID取得用ログ
    logger.info("SOURCE_TYPE: %s", source_type)

    if group_id:
        logger.info("LINE_GROUP_ID: %s", group_id)

    if room_id:
        logger.info("LINE_ROOM_ID: %s", room_id)

    if user_id:
        logger.info("LINE_USER_ID: %s", user_id)

    # メッセージ本文
    user_text = event.message.text.strip()

    logger.info("Received LINE text message")

    # ----------------------------------------------
    # ヘルプ
    # ----------------------------------------------

    if user_text == "!ヘルプ":
        response_text = (
            "【IIDX課題曲Bot コマンド一覧】\n\n"
            "!ヘルプ\n"
            "コマンド一覧を表示します。\n\n"
            "!課題曲\n"
            "このグループの最新課題曲を表示します。\n\n"
            "!課題曲ランダム\n"
            "☆5・☆6・☆7のランダム課題曲を表示します。"
        )

    # ----------------------------------------------
    # 最新の課題曲
    # ----------------------------------------------

    elif user_text == "!課題曲":
        try:
            response_text = get_task_song(group_id)

        except Exception:
            logger.exception("課題曲の取得に失敗しました")
            response_text = (
                "課題曲の取得中にエラーが発生しました。\n"
                "管理者はRenderのログを確認してください。"
            )

    # ----------------------------------------------
    # ランダム課題曲
    # ----------------------------------------------

    elif user_text == "!課題曲ランダム":
        try:
            response_text = get_random_song()

        except Exception:
            logger.exception("ランダム課題曲の取得に失敗しました")
            response_text = (
                "ランダム課題曲の取得中にエラーが発生しました。\n"
                "管理者はRenderのログを確認してください。"
            )

    # ----------------------------------------------
    # 対象外のメッセージ
    # ----------------------------------------------

    else:
        return

    # ----------------------------------------------
    # LINEに返信
    # ----------------------------------------------

    reply_message(
        event.reply_token,
        response_text,
    )


# ==================================================
# ローカル実行用
# Renderでは通常、Gunicornから起動する
# ==================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
    )
