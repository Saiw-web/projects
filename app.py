import asyncio
from pyrogram import Client, filters
from pyrogram.errors import InviteHashExpired, InviteHashInvalid
from flask import Flask, request, render_template, redirect, url_for

# Данные API
api_id = 20222139
api_hash = 'f70b6f4d69dcdacaf921eee2e0e9cdab'

app = Client("my_account", api_id=api_id, api_hash=api_hash)
web_app = Flask(__name__)

# Глобальные переменные
user_chats = {}
messages_to_send = 0
message_delay = 10
cancel_sending = False

@web_app.route('/')
def index():
    return render_template('index.html', user_chats=user_chats, message_delay=message_delay)

@web_app.route('/add_chat', methods=['POST'])
async def add_chat():
    link = request.form['link']
    try:
        chat = await app.join_chat(link)
        chat_link = f"https://t.me/{chat.username}" if chat.username else f"Неизвестная группа ({chat.id})"
        user_chats[chat.id] = chat_link
        return redirect(url_for('index'))
    except (InviteHashExpired, InviteHashInvalid):
        return "Ошибка: ссылка приглашения недействительна или истекла."

@web_app.route('/send_message', methods=['POST'])
async def send_message():
    global messages_to_send, cancel_sending
    chat_link = request.form['chat_link']
    chat_id = next((id for id, link in user_chats.items() if link == chat_link), None)

    messages_to_send = int(request.form['messages_to_send'])
    message_text = request.form['message_text']

    cancel_sending = False
    if chat_id:
        for i in range(messages_to_send):
            if cancel_sending:
                break
            await asyncio.sleep(message_delay)
            await app.send_message(chat_id, message_text)
        return redirect(url_for('index'))
    return "Ошибка: не удалось найти ID группы."

@web_app.route('/set_delay', methods=['POST'])
def set_delay():
    global message_delay
    message_delay = int(request.form['delay'])
    return redirect(url_for('index'))

@web_app.route('/cancel', methods=['POST'])
def cancel():
    global cancel_sending
    cancel_sending = True
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.start()
    web_app.run(debug=True, host='0.0.0.0', port=5000)
    app.stop()