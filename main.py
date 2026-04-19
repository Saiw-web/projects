import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import InviteHashExpired, InviteHashInvalid

# Данные API
api_id = 20222139
api_hash = 'f70b6f4d69dcdacaf921eee2e0e9cdab'
bot_token = '6620225533:AAGxAcKvxvLeK-wZZ3lvyD9psnIGviZbTCM'

# Создание клиентов
bot_app = Client("bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
user_app = Client("user", api_id=api_id, api_hash=api_hash)

user_chats = {}
cancel_sending = False

async def initialize_user_app():
    """Инициализация user_app с запросом на ввод номера телефона и кода подтверждения."""
    print("Запуск клиента пользователя (user_app)...")
    await user_app.start()
    print("user_app успешно запущен.")

async def initialize_bot_app():
    """Инициализация bot_app с использованием токена бота."""
    print("Запуск клиента бота (bot_app)...")
    await bot_app.start()
    print("bot_app успешно запущен.")

async def add_chat_by_link(link, message_text, count, delay):
    print(f"Попытка присоединиться к чату по ссылке: {link}")
    try:
        # Присоединяемся к чату с аккаунта пользователя
        chat = await user_app.join_chat(link)
        chat_link = f"https://t.me/{chat.username}" if chat.username else f"Неизвестная группа ({chat.id})"
        user_chats[chat.id] = {'link': chat_link, 'message': message_text, 'count': count, 'delay': delay}
        print(f"Успешно присоединились к чату: {chat_link}")
        return f"Вы присоединились к чату: {chat_link} с сообщением: '{message_text}' (Количество отправок: {count}, Задержка: {delay} секунд)"
    except (InviteHashExpired, InviteHashInvalid):
        print("Ошибка: Ссылка недействительна или срок её действия истёк.")
        return "Ошибка: ссылка приглашения недействительна или срок её действия истёк."

async def send_messages_to_groups():
    global cancel_sending
    cancel_sending = False

    if not user_chats:
        print("Нет доступных групп для отправки сообщений.")
        return "Нет доступных групп для отправки сообщений."

    print("Начинаем отправку сообщений в группы...")
    async def send_message(chat_id, chat_info):
        for i in range(chat_info['count']):
            if cancel_sending:
                print("Отправка сообщений была отменена.")
                return "Отправка сообщений была отменена."
            await asyncio.sleep(chat_info['delay'])
            await user_app.send_message(chat_id, chat_info['message'])
            print(f"Сообщение {i + 1}/{chat_info['count']} отправлено в группу: {chat_info['link']}")

    await asyncio.gather(*(send_message(chat_id, chat_info) for chat_id, chat_info in user_chats.items()))
    print("Все сообщения успешно отправлены.")
    return "Все сообщения успешно отправлены."

def create_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Добавить группу", callback_data="add")],
        [InlineKeyboardButton("Отправить сообщения", callback_data="send")],
        [InlineKeyboardButton("Просмотреть группы", callback_data="view")],
        [InlineKeyboardButton("Удалить группу", callback_data="remove")],
        [InlineKeyboardButton("Отменить отправку", callback_data="cancel")]
    ])

@bot_app.on_message(filters.command("start"))
async def start_command(client, message):
    print("Получена команда /start")
    await message.reply("Добро пожаловать! Используйте кнопки для управления ботом:", reply_markup=create_main_keyboard())

@bot_app.on_callback_query(filters.regex("add"))
async def add_callback(client, callback_query):
    print("Получен запрос на добавление группы.")
    await callback_query.answer("Введите данные в формате: ссылка сообщение количество задержка (через пробелы)")
    response = await bot_app.listen(callback_query.message.chat.id)
    try:
        link, message_text, count, delay = response.text.split()
        count = int(count)
        delay = int(delay)
        result = await add_chat_by_link(link, message_text, count, delay)
    except ValueError:
        result = "Ошибка: Введите корректные данные."
        print("Ошибка: Введены некорректные данные.")
    await callback_query.message.reply(result)

@bot_app.on_callback_query(filters.regex("send"))
async def send_callback(client, callback_query):
    print("Получен запрос на отправку сообщений в группы.")
    result = await send_messages_to_groups()
    await callback_query.message.reply(result)

@bot_app.on_callback_query(filters.regex("view"))
async def view_callback(client, callback_query):
    print("Получен запрос на просмотр доступных групп.")
    if not user_chats:
        await callback_query.message.reply("Нет доступных групп.")
        print("Нет доступных групп.")
    else:
        group_info = "\n".join([f"{chat_id}: {info['link']}, Сообщение: {info['message']}, Кол-во: {info['count']}, Задержка: {info['delay']} секунд" for chat_id, info in user_chats.items()])
        await callback_query.message.reply(f"Доступные группы:\n{group_info}")
        print(f"Список доступных групп:\n{group_info}")

@bot_app.on_callback_query(filters.regex("remove"))
async def remove_callback(client, callback_query):
    print("Получен запрос на удаление группы.")
    await callback_query.answer("Введите ID группы для удаления:")
    response = await bot_app.listen(callback_query.message.chat.id)
    try:
        chat_id = int(response.text)
        if chat_id in user_chats:
            del user_chats[chat_id]
            await callback_query.message.reply("Группа успешно удалена.")
            print(f"Группа с ID {chat_id} успешно удалена.")
        else:
            await callback_query.message.reply("Ошибка: Группа с таким ID не найдена.")
            print("Ошибка: Группа с указанным ID не найдена.")
    except ValueError:
        await callback_query.message.reply("Ошибка: Введите числовой ID группы.")
        print("Ошибка: Введен некорректный ID группы.")

@bot_app.on_callback_query(filters.regex("cancel"))
async def cancel_callback(client, callback_query):
    global cancel_sending
    cancel_sending = True
    print("Отправка сообщений отменена пользователем.")
    await callback_query.message.reply("Процесс отправки сообщений будет остановлен.")

# Запуск клиентов
async def main():
    try:
        print("Инициализация user_app...")
        await initialize_user_app()
        print("user_app успешно запущен.")

        print("Инициализация bot_app...")
        await initialize_bot_app()
        print("bot_app успешно запущен.")

        print("Бот и клиент пользователя успешно запущены. Ожидание событий...")
        await asyncio.Event().wait()

    except Exception as e:
        print(f"Ошибка при запуске: {e}")

    finally:
        await user_app.stop()
        await bot_app.stop()
        print("Остановка бота и клиента пользователя завершена.")

if __name__ == "__main__":
    asyncio.run(main())