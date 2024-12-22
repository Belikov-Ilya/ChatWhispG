import asyncio
import logging
import sqlite3
import json
import os
from aiogram import Bot, Dispatcher, Router, types
from aiogram.client.default import DefaultBotProperties
import config
import train
import time

from admin import admin_router

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и маршрутизатора
bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
router = Router()
dispatcher = Dispatcher()
dispatcher.include_router(router)
dispatcher.include_router(admin_router)

# Создание базы данных
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS message_queue (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER NOT NULL,
                        message_id INTEGER NOT NULL,
                        message_text TEXT NOT NULL,
                        is_processed INTEGER DEFAULT 0
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS statistics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp INTEGER NOT NULL,
                        type TEXT DEFAULT 'normal'
                    )''')
    conn.commit()
    conn.close()

init_db()

# Обновление статистики
def update_statistics(message_type):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    timestamp = int(time.time())
    cursor.execute("INSERT INTO statistics (timestamp, type) VALUES (?, ?)", (timestamp, message_type))
    conn.commit()
    conn.close()

# Добавление сообщения в датасет
def add_to_dataset(category, text):
    if text.startswith("⚠️ Нарушение: Нецензурная брань. Текст: ") or text.startswith("⚠️ Нарушение: Реклама. Текст: "):
        text = text.replace("⚠️ Нарушение: Нецензурная брань. Текст: ", "")
        text = text.replace("⚠️ Нарушение: Реклама. Текст: ", "")
    file_path = f"dataset/{category}.json"
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump([], file, ensure_ascii=False, indent=4)

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    data.append(text)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    logger.info(f"Сообщение добавлено в датасет {file_path}: {text}")

@router.message(lambda message: message.text and message.text.startswith("/add"))
async def handle_add_command(message: types.Message):
    try:
        # Извлечение категории
        command_parts = message.text.split(" ", 1)
        if len(command_parts) < 2:
            await message.reply("Укажите категорию в формате: /add <category>")
            return

        category = command_parts[1]

        # Проверка наличия текста в ответе
        if not message.reply_to_message or not message.reply_to_message.text:
            await message.reply("Сообщение, на которое вы ответили, не содержит текста.")
            return
        mess = message.reply_to_message.text
        add_to_dataset(category, mess)

        # Отправка подтверждения
        await message.reply(f"Сообщение добавлено в датасет {category}.")

        # Переобучение модели
        await train.train_model()
        logger.info("Модели переобучены.")
        await message.reply("Модели успешно переобучены на обновленных данных.")

    except Exception as e:
        logger.error(f"Ошибка обработки команды /add: {e}")
        await message.reply("Произошла ошибка при добавлении сообщения в датасет.")

# Добавление сообщения в базу данных
@router.message(lambda message: message.chat.id in config.ALLOWED_CHATS)
async def handle_message(message: types.Message):
    if message.text:
        logger.info(f"Получено сообщение из чата {message.chat.id}: {message.text}")
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        try:
            # Проверяем данные перед записью
            if not isinstance(message.chat.id, int) or not isinstance(message.message_id, int) or not message.text.strip():
                logger.error(f"Invalid message data: chat_id={message.chat.id}, message_id={message.message_id}, text={message.text}")
                return

            cursor.execute("INSERT INTO message_queue (chat_id, message_id, message_text) VALUES (?, ?, ?)",
                           (message.chat.id, message.message_id, message.text.strip()))
            conn.commit()
        except Exception as e:
            logger.error(f"Ошибка при добавлении сообщения в очередь: {e}")
        finally:
            conn.close()

# Очередь сообщений
async def process_queue():
    while True:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, chat_id, message_id, message_text FROM message_queue WHERE is_processed = 0 LIMIT 30")
        rows = cursor.fetchall()

        for row in rows:
            msg_id, chat_id, message_id, text = row
            try:
                # Проверяем данные из базы перед обработкой
                if not isinstance(chat_id, int) or not isinstance(message_id, int) or not isinstance(text, str) or not text.strip():
                    logger.error(f"Invalid data in queue: id={msg_id}, chat_id={chat_id}, message_id={message_id}, text={text}")
                    cursor.execute("UPDATE message_queue SET is_processed = 1 WHERE id = ?", (msg_id,))
                    continue

                violation_type = await train.detect_profanity_or_ad(text.strip())
                if violation_type == "Нецензурная брань":
                    reply_text = f"⚠️ Нарушение: Нецензурная брань. Текст: {text[:50]}"
                    update_statistics("violation_profanity")
                elif violation_type == "Реклама":
                    reply_text = f"⚠️ Нарушение: Реклама. Текст: {text[:50]}"
                    update_statistics("violation_ad")
                else:
                    reply_text = "✅ Сообщение без нарушений."
                    update_statistics("normal")

                await bot.send_message(chat_id, reply_text, reply_to_message_id=message_id)
                cursor.execute("UPDATE message_queue SET is_processed = 1 WHERE id = ?", (msg_id,))
            except Exception as e:
                logger.error(f"Error processing message: {e}. Data: id={msg_id}, chat_id={chat_id}, message_id={message_id}, text={text}")
                cursor.execute("UPDATE message_queue SET is_processed = 1 WHERE id = ?", (msg_id,))

        conn.commit()
        conn.close()
        await asyncio.sleep(1 / config.REPLY_RATE)

# Основная функция запуска
async def main():
    logger.info("Инициализация системы")
    asyncio.create_task(train.monitor_dataset_changes())
    asyncio.create_task(process_queue())

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        logger.info("Запуск диспетчера")
        await dispatcher.start_polling(bot)
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())