from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    TemplateSendMessage, MessageAction, ButtonsTemplate
)

import os
import re
import sqlite3
from datetime import datetime
app = Flask(__name__)
STATUS = ''
UPDATENAME = ''
UPDATEKEY = ''
TABLE_DIC = {"身長":"height", "体重":"weight", "生年月日":"dateofbirth", "性格":"personality"}

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
    global UPDATENAME

    if event.message.text == '登録':
        button_message = add_info()
        line_bot_api.reply_message(event.reply_token,
                                  button_message
                                  )
    elif event.message.text == '確認':
        button_message = confirm()
        line_bot_api.reply_message(event.reply_token,
                                  button_message
                                  )



    if event.message.text == '新規登録':
        STATUS = '新規登録'
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=STATUS+'情報を入力してください')
            )

    elif event.message.text == "介護日誌登録":
        STATUS = "介護日誌登録"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='介護日誌を登録したい人の名前を入力してください')
            )
    elif event.message.text == '利用者情報':
        STATUS = '利用者情報'
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=STATUS+'したい人の名前を教えてください')
            )
    elif event.message.text == '介護日誌確認':
        STATUS = "介護日誌確認"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='介護日誌を確認したい人の名前を入力してください')
            )

    elif event.message.text == '削除':
        STATUS = '削除'
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='情報を'+STATUS+'したい人の名前を教えてください')
            )

    elif event.message.text == '更新':
        STATUS = '更新'
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='情報を'+STATUS+'したい人の名前を教えてください')
            )

    else:
        if STATUS == '新規登録':
            message = register(event.message.text)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=message)
                )
            STATUS = ''

        elif STATUS == '介護日誌登録':

            UPDATENAME = event.message.text
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='内容を入力してください')
                )
            STATUS = '介護日誌登録2'

        elif STATUS == '介護日誌登録2':
            message = register_diary(UPDATENAME, event.message.text)
            if message == None:
                message = 'その人は存在しません'
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=message)
                )
            STATUS = ''

        elif STATUS == '利用者情報':
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

        elif STATUS == '介護日誌確認':
            UPDATENAME = event.message.text
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='確認する日付を入力してください')
                )
            STATUS = '介護日誌確認2'

        elif STATUS == '介護日誌確認2':
            message = ''
            result = check_diary(UPDATENAME, event.message.text)
            if result == None:
                message = 'その人は存在しません'
            else:
                message = result
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=message)
                )
            STATUS = ''

        elif STATUS == '削除':
            name = event.message.text
            message = ''
            result = delete_info(name)

            if result == None:
                message = 'その人は存在しません'
            else:
                message = result[0]+"さんの情報を削除しました"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=message)
                )
            STATUS = ''

        elif STATUS == '更新':
            name = event.message.text
            UPDATENAME = name
            button_message = update_button(name)
            line_bot_api.reply_message(
                event.reply_token,
                button_message
                )
            STATUS = '更新2'

        elif STATUS == '更新2':
            global UPDATEKEY
            UPDATEKEY = event.message.text
            button_message = update_button(UPDATENAME)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text = "内容を入力してください")
                )
            STATUS = '更新3'

        elif STATUS == '更新3':
            result = update_info(UPDATENAME, UPDATEKEY, event.message.text)
            if result == None:
                message = 'その人は存在しません'
            else:
                message = result[0]+"さんの"+UPDATEKEY+"を"+event.message.text+"に更新しました"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=message)
                )
            STATUS = ''


        button_message = make_button_template()
        line_bot_api.reply_message(
                event.reply_token,
                # TextSendMessage(text='行いたい操作を選択してください(e.g. 登録 確認)')
                button_message
                )

#TODO 名前が一意ではないので、重複したデータがある際のエラーhandlingが必要
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

def check_diary(name, date):
    dbname = 'info.db'
    conn = sqlite3.connect(dbname)
    c = conn.cursor()
    select_sql = "select id, name from userinfo where name like '%"+name+"%'"
    c.execute(select_sql)
    result = c.fetchone()
    if result == None:
        return None
    id, name = result[0], result[1]
    select_sql = "select id, date, note from note where date=='"+date+"' and id=='"+str(id)+"'"
    c.execute(select_sql)
    result = c.fetchone()
    conn.close()
    if not (result == None):
        id, date, note = result
        result = '登録id: '+str(id)+'\n'+name+'さん\n'+date+'\n介護日誌:\n'+note
    return result

#TODO 必要情報が抜けている時の処理
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

def register_diary(name, text):
    dbname = 'info.db'
    conn = sqlite3.connect(dbname)
    c = conn.cursor()
    select_sql = "select id from userinfo where name like '%"+name+"%'"
    c.execute(select_sql)
    result = c.fetchone()
    if result == None:
        return None
    id = result[0]
    sql = "insert into note (id, date, note) values (?,?,?)"
    info = (id,datetime.now().strftime("%Y/%m/%d"), text)
    conn.execute(sql, info)
    conn.commit()
    conn.close()
    return '完了'


#TODO 本当に削除するかの確認を取る
def delete_info(name):
    dbname = 'info.db'
    conn = sqlite3.connect(dbname)
    c = conn.cursor()
    select_sql = "select name from userinfo where name like '%"+name+"%'"
    c.execute(select_sql)
    result = c.fetchone()
    sql = "delete from userinfo where name like '%"+name+"%'"
    conn.execute(sql)
    conn.commit()
    conn.close()
    return result

def update_info(name, key, val):
    dbname = 'info.db'
    conn = sqlite3.connect(dbname)
    c = conn.cursor()
    select_sql = "select name from userinfo where name like '%"+name+"%'"
    c.execute(select_sql)
    result = c.fetchone()
    sql = "update userinfo set "+TABLE_DIC[key]+" ='"+str(val)+"' where name like '%"+name+"%'"
    conn.execute(sql)
    conn.commit()
    conn.close()
    return result

#TODO 必要情報が抜けている時の処理
def extract(text):
    table = re.sub('介.*\n|1利用.*\n|2身長.*\n|3体重.*\n|4生年月日.*\n|5持.*\n|6特.*\n','',text)
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




def make_button_template():
    message_template = TemplateSendMessage(
        alt_text="行いたい操作を選択してください",
        template=ButtonsTemplate(
            text="行いたい操作を選択してください",
            actions=[
                MessageAction(
                    label="登録",
                    text="登録"
                ),
                MessageAction(
                    label="確認",
                    text="確認"
                ),
                MessageAction(
                    label="削除",
                    text="削除"
                ),
                MessageAction(
                    label="更新",
                    text="更新"
                ),
            ]
        )
    )
    return message_template

def confirm():
    confirm_button = TemplateSendMessage(
        alt_text="どちらの情報を確認しますか",
        template=ButtonsTemplate(
            text="どちらの情報を確認しますか",
            actions=[
                MessageAction(
                    label="利用者情報",
                    text="利用者情報"
                ),
                MessageAction(
                    label="介護日誌確認",
                    text="介護日誌確認"
                ),
            ]
        )
    )
    return confirm_button

def add_info():
    add_button = TemplateSendMessage(
        alt_text="どちらの情報を登録しますか",
        template=ButtonsTemplate(
            text="どちらの情報を登録しますか",
            actions=[
                MessageAction(
                    label="新規登録",
                    text="新規登録"
                ),
                MessageAction(
                    label="介護日誌登録",
                    text="介護日誌登録"
                ),
            ]
        )
    )
    return add_button

def update_button(name):
    add_button = TemplateSendMessage(
        alt_text=name+"さんのどちらの情報をアップデートしますか",
        template=ButtonsTemplate(
            text=name+"さんのどちらの情報をアップデートしますか",
            actions=[
                MessageAction(
                    label="身長",
                    text="身長"
                ),
                MessageAction(
                    label="体重",
                    text="体重"
                ),
                MessageAction(
                    label="生年月日",
                    text="生年月日"
                ),
                MessageAction(
                    label="性格",
                    text="性格"
                )
            ]
        )
    )
    return add_button
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
