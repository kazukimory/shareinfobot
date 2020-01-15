from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    TemplateSendMessage, MessageAction, ConfirmTemplate
)

import os
import re
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
            TextSendMessage(text=STATUS+'したい人の名前を教えてください')
            )
    else:
        if STATUS == '登録':
            message = register(event.message.text)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=message)
                )
            STATUS = ''

        elif STATUS == '確認':
            name = event.message.text
            message = ''
            result = check(name)

            if result == None:
                message = 'その人は存在しません'
            else:
                message = result
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=message)
                )
            STATUS = ''
        
        confirm_message = make_confirm_template()
        line_bot_api.reply_message(
                event.reply_token,
                # TextSendMessage(text='行いたい操作を選択してください(e.g. 登録 確認)')
                confirm_message
                )

def check(name):
    dbname = 'info.db'
    conn = sqlite3.connect(dbname)
    c = conn.cursor()
    select_sql = "select * from userinfo where name like '%"+name+"%'"
    c.execute(select_sql)
    result = c.fetchone()
    conn.close()
    if not (result == None):
        id, name, height, weight, dateofbirth, personality = result
        result = '介護者情報\nid: '+str(id)+'\n利用者氏名\n'+name+'\n身長\n'+str(height)+'cm\n'+'体重\n'+str(weight)+'\n生年月日\n'+dateofbirth+'\n特徴&持病\n'+personality
    return result


def register(text):
    dbname = 'info.db'
    conn = sqlite3.connect(dbname)
    name, height, weight, dateofbirth, personality = extract(text)
    sql = 'insert into userinfo (name, height, weight, dateofbirth, personality) values (?,?,?,?,?)'
    info = (name, height, weight, dateofbirth, personality)
    conn.execute(sql, info)
    conn.commit()
    conn.close()
    return '完了'

def extract(text):
    table=re.sub('介護者情報書\n|1利用者氏名\n|2身長\(cm\)\(cmは記入不要\)\n|3体重\(kg\)\(kgは記入不要\)\n|4生年月日\(西暦\)\n|5持病\n|6特徴\n','',text)
    new_table=table.splitlines()
    name, height, weight, a, b, c, disease, personality = new_table
    birth = [a, b, c]

    list = ["", "", ""]
    for k in birth:
        if '年' in k:
            list[0] = k
        elif '月' in k:
            list[1] = k
        elif '日' in k:
            list[2] = k

    DOB_tmp2 = '/'.join(list)
    DOB=re.sub('年|月|日','',DOB_tmp2)

    return name, height, weight, DOB, personality + '\n' + disease
    

def make_confirm_template():
    message_template = TemplateSendMessage(
        alt_text="表示できない",
        template=ConfirmTemplate(
            text="介護利用者登録フォーマット",
            actions=[
                MessageAction(
                    label="登録",
                    text="登録"
                ),
                MessageAction(
                    label="確認",
                    text="確認"
                )
            ]
        )
    )
    return message_template

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
