最高！！🎉
これでRenderにLINEの認証情報を登録できたね！

いよいよ、弐寺Botをインターネット上で動かすよ！

🚀 STEP 10：Botをデプロイする
① デプロイを開始する

Renderの設定画面で、「Deploy Web Service」 をクリックしてね。

これでRenderがGitHubからプログラムを取得して、Botを起動するための準備を始めるよ。

② デプロイの進行状況を確認する

クリックすると、ログ（処理の記録）が表示されるはずだよ。

最初はライブラリのインストールなどが実行されるので、少し待とう。

画面に次のような表示が出れば成功の目安だよ。

Build successful
Deploy live

※ 表示内容は画面によって異なる場合があるよ。

③ Botが起動したか確認する

デプロイが成功したら、Renderの画面にサービスのURLが表示されるよ。

例えば、次のような形式だよ。

https://iidx-line-bot.onrender.com

これは例なので、実際に表示されたURLを使ってね。

そのURLをブラウザで開いたときに、

弐寺Bot is running!

と表示されれば、Webサーバーが起動していることを確認できるよ！

⚠️ もしエラーが出たら

慌てなくて大丈夫！

Renderの画面にエラーが表示された場合は、エラーの文章をコピーするか、スクリーンショットを送ってね。

チャネルシークレットやアクセストークンが写っていたら、隠してから送ってね。

🙋 次の確認！

デプロイを開始したら、どの状態になったか教えて！

A：Deploy live と表示された！
B：デプロイ中で、まだ終わっていない
C：エラーが表示された

ここまで来たら、あと少し！

次はLINEのWebhookを設定して、実際にBotから返信が届くかテストしよう！ 💪

LINE友達追加確認 からのブランチ

エラー

画像を確認しました。エラーの原因が分かりました！

GitHubの app.py に記載されているコードの14行目に、文法の間違いがあります。

① エラーの原因

Renderのログに次のエラーが表示されています。

app = Flask(**name**)

本来は次のように書く必要があります。

app = Flask(__name__)

**（アスタリスク）ではなく、__（アンダースコア2個）を使います。

② GitHubで修正する
GitHub を開く
弐寺Botのリポジトリを開く
app.py をクリック
右上の鉛筆マーク（Edit）をクリック
14行目を次のコードに修正する

修正後のコード [コピー]

app = Flask(__name__)
Commit changes... をクリック
Commit changes で保存する
③ Renderで再デプロイする

GitHubの変更を保存すると、Renderの自動デプロイが有効なら再デプロイが始まります。

自動で始まらない場合は、Renderで次の操作をしてください。

Renderで弐寺Botのサービスを開く
Manual Deploy をクリック
Deploy latest commit を選択する

これで修正したコードが反映されます。

次の確認

修正後、Renderの状態を教えてください。

Deploy live（成功）になった

別のエラーが表示された

まだデプロイ中

[回答する]

成功したら、次はLINE DevelopersにWebhook URLを登録して、実際にBotから返信が来るかテストします。

画像を確認しました。今回も原因が特定できました。

app.py の23行目で、インデント（行頭の空白）が不足しています。

① エラーの原因

Renderには次のエラーが表示されています。

IndentationError: expected an indented block
after function definition on line 22

Pythonでは、関数の中の処理を半角スペース4つ分、右にずらす必要があります。

修正前（エラー）

def callback():
signature = request.headers.get("X-Line-Signature", "")

修正後（正しい書き方）

def callback():
    signature = request.headers.get("X-Line-Signature", "")
② 今回は app.py 全体を修正しましょう

前回も文法エラーが発生しているため、ほかの行にも記述ミスがある可能性があります。

確実に修正できるよう、以下のコードで app.py の内容をすべて置き換えることをおすすめします。

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

app = Flask(__name__)

channel_secret = os.environ["LINE_CHANNEL_SECRET"]
channel_access_token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]

handler = WebhookHandler(channel_secret)

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    configuration = Configuration(
        access_token=channel_access_token
    )

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(
                        text="弐寺Botがメッセージを受信しました！"
                    )
                ],
            )
        )

@app.route("/", methods=["GET"])
def home():
    return "弐寺Bot is running!"
③ GitHubで保存する
GitHubで app.py を開く
鉛筆マークをクリック
既存のコードをすべて削除
上記コードをそのまま貼り付ける
Commit changes... をクリックして保存

Renderの自動デプロイが有効なら、変更後に再デプロイが始まります。

④ 結果を確認する

Deploy live と表示された

またエラーが出た

まだデプロイ中

[回答する]

Deploy live になったら、次はいよいよ LINEとRenderを接続してBotを動作確認します。

これは ChatGPT と taiga tamada との会話です。応答するとブランチが作成されます。
