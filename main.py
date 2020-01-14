from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
import os

import sqlite3

dbname = 'info.db'
app = Flask(__name__)
conn = sqlite3.connect(dbname)
c = conn.cursor()

#環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # if event.message.text == '登録':
    #     sql = 'insert into userinfo (id, name, height, weight, dateofbirth, personality) values (?,?,?,?,?,?)'
    #     info = (1, "michael", 164, 70, "1998年5月6日", "二重国籍")
    #     conn.execute(sql, info)

    #     conn.commit()

    #     select_sql = 'select * from userinfo'

    #     c.execute(select_sql)
    #     result = c.fetchone()
    #     conn.close()
    #     message =''

    message = ''
    select_sql = 'select * from userinfo'
    c.execute(select_sql)
    line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=message)
            )
    result = c.fetchone()
    conn.close()

    for text in result:
        message=message+str(text)



if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)