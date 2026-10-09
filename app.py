import os
from flask import Flask, request, abort
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

app = Flask(**name**)

channel_secret = os.environ.get("LINE_CHANNEL_SECRET", "")
channel_access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")

handler = WebhookHandler(channel_secret)

@app.route("/callback", methods=["POST"])
def callback():
signature = request.headers.get("X-Line-Signature", "")
body = request.get_data(as_text=True)

```
try:
    handler.handle(body, signature)
except InvalidSignatureError:
    abort(400)

return "OK"
```

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
configuration = Configuration(
access_token=channel_access_token
)

```
with ApiClient(configuration) as api_client:
    line_bot_api = MessagingApi(api_client)

    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[
                TextMessage(text="弐寺Botだよ！メッセージを受信したよ！")
            ],
        )
    )
```

@app.route("/", methods=["GET"])
def home():
return "弐寺Bot is running!"

