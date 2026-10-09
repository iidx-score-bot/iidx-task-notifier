import os
import random

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
from linebot.v3.webhooks import MessageEvent, TextMessageContent

app = Flask(__name__)

# LINEの接続設定
channel_secret = os.environ["LINE_CHANNEL_SECRET"]
channel_access_token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]

handler = WebhookHandler(channel_secret)

# Supabaseの接続設定
supabase_url = os.environ["SUPABASE_URL"]
supabase_key = os.environ["SUPABASE_SECRET_KEY"]

supabase = create_client(supabase_url, supabase_key)


@app.route("/", methods=["GET"])
def home():
    return "弐寺Bot is running!"


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.warning("LINE signature verification failed")
        abort(400)

    return "OK"


def get_task_song():
    # 最新の課題曲を取得
    task_response = (
        supabase.table("tasks")
        .select("chart_id,task_date,note")
        .eq("group_id", "test-group")
        .order("task_date", desc=True)
        .limit(1)
        .execute()
    )

    if not task_response.data:
        return "課題曲が登録されていません。"

    task = task_response.data[0]

    # 譜面情報を取得
    chart_response = (
        supabase.table("charts")
        .select("song_id,play_style,difficulty,level")
        .eq("id", task["chart_id"])
        .limit(1)
        .execute()
    )

    if not chart_response.data:
        return "課題曲に対応する譜面が見つかりません。"

    chart = chart_response.data[0]

    # 楽曲情報を取得
    song_response = (
        supabase.table("songs")
        .select("title,artist")
        .eq("id", chart["song_id"])
        .limit(1)
        .execute()
    )

    if not song_response.data:
        return "課題曲に対応する楽曲が見つかりません。"

    song = song_response.data[0]

    return (
        "【弐寺Bot 課題曲】\n\n"
        f"曲名：{song['title']}\n"
        f"アーティスト：{song['artist']}\n"
        f"譜面：{chart['play_style']} {chart['difficulty']}\n"
        f"レベル：{chart['level']}\n"
        f"課題日：{task['task_date']}\n"
        f"メモ：{task['note'] or 'なし'}"
    )


def get_random_song():
    # 登録されている譜面を取得
    chart_response = (
        supabase.table("charts")
        .select("id,song_id,play_style,difficulty,level")
        .execute()
    )

    charts = chart_response.data

    if not charts:
        return "選曲できる譜面が登録されていません。"

    # 譜面からランダムに1件選ぶ
    chart = random.choice(charts)

    # 楽曲情報を取得
    song_response = (
        supabase.table("songs")
        .select("title,artist")
        .eq("id", chart["song_id"])
        .limit(1)
        .execute()
    )

    if not song_response.data:
        return "選択した譜面に対応する楽曲が見つかりません。"

    song = song_response.data[0]

    return (
        "【弐寺Bot ランダム選曲】\n\n"
        f"曲名：{song['title']}\n"
        f"アーティスト：{song['artist']}\n"
        f"譜面：{chart['play_style']} {chart['difficulty']}\n"
        f"レベル：{chart['level']}"
    )


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_text = event.message.text.strip()

    if user_text == "!ヘルプ":
        reply_text = (
            "【弐寺Bot コマンド一覧】\n"
            "!ヘルプ：コマンド一覧\n"
            "!課題曲：現在の課題曲を確認\n"
            "!課題曲ランダム：ランダムに譜面を選ぶ"
        )

    elif user_text == "!課題曲":
        try:
            reply_text = get_task_song()
        except Exception:
            app.logger.exception("Supabase task retrieval failed")
            reply_text = "課題曲の取得中にエラーが発生しました。"

    elif user_text == "!課題曲ランダム":
        try:
            reply_text = get_random_song()
        except Exception:
            app.logger.exception("Random song retrieval failed")
            reply_text = "ランダム選曲中にエラーが発生しました。"

    else:
        return

    configuration = Configuration(
        access_token=channel_access_token
    )

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)],
            )
        )
