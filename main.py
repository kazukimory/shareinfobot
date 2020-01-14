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
app = Flask(__name__)
STATUS = ''

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
    global STATUS
    if event.message.text == '登録':
        STATUS = '登録'
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=STATUS+'情報を入力してください')
            )

    elif event.message.text == '確認':
        STATUS = '確認'
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=SATTUS+'したい人の名前を教えてください')
            )

    if STATUS == '登録':
        message = register()
        STATUS = ''
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=message)
            )

    elif STATUS == '確認':
        name = event.message.text
        message = ''
        result = check(name)

        if result == None:
            message = 'その人は存在しません'
        else:
            for text in result:
                message=message+str(text)+' '
        STATUS = ''
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=message)
            )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='行いたい操作を選択してください(e.g. 登録 確認)')
            )

def split(event):
    return 'test'

def check(name):
    dbname = 'info.db'
    conn = sqlite3.connect(dbname)
    c = conn.cursor()
    select_sql = "select * from userinfo where name like '%"+name+"%'"
    c.execute(select_sql)
    result = c.fetchone()
    conn.close()
    return result


def register():
    dbname = 'info.db'
    conn = sqlite3.connect(dbname)
    '''test'''
    id = 2
    name = 'yuhi matsuo'
    height = 165
    weight = 58
    dateofbirth = '1998/12/08'
    personality = '真面目'
    '''--------'''
    sql = 'insert into userinfo (id, name, height, weight, dateofbirth, personality) values (?,?,?,?,?,?)'
    info = (id, name, height, weight, dateofbirth, personality)
    conn.execute(sql, info)
    conn.commit()
    conn.close()
    return '完了'

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)