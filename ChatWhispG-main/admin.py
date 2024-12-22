from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import config
import sqlite3
import logging
import time

logger = logging.getLogger(__name__)
admin_router = Router()

@admin_router.message(lambda message: message.text.startswith('/admin'))
async def handle_admin(message: types.Message):
    if message.from_user.id not in config.ADMINS:
        logger.info(f"Пользователь {message.from_user.id} пытался вызвать /admin без прав")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{'✅' if config.FILTER_PROFANITY else '❌'} Брань",
            callback_data="toggle_profanity"
        )],
        [InlineKeyboardButton(
            text=f"{'✅' if config.FILTER_ADVERTISING else '❌'} Реклама",
            callback_data="toggle_ad"
        )],
        [InlineKeyboardButton(
            text="📊 Статистика",
            callback_data="show_statistics"
        )]
    ])

    await message.reply("Панель администратора:", reply_markup=keyboard)

@admin_router.callback_query(lambda c: c.data in ["toggle_profanity", "toggle_ad", "show_statistics"])
async def handle_admin_buttons(callback: CallbackQuery):
    if callback.data == "toggle_profanity":
        config.FILTER_PROFANITY = not config.FILTER_PROFANITY
        logger.info(f"Фильтр брани переключен: {'Включен' if config.FILTER_PROFANITY else 'Отключен'}")
        await callback.message.edit_text(
            f"Фильтр брани: {'✅ Включен' if config.FILTER_PROFANITY else '❌ Отключен'}"
        )

    elif callback.data == "toggle_ad":
        config.FILTER_ADVERTISING = not config.FILTER_ADVERTISING
        logger.info(f"Фильтр рекламы переключен: {'Включен' if config.FILTER_ADVERTISING else 'Отключен'}")
        await callback.message.edit_text(
            f"Фильтр рекламы: {'✅ Включен' if config.FILTER_ADVERTISING else '❌ Отключен'}"
        )

    elif callback.data == "show_statistics":
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # Ensure necessary table exists
        cursor.execute("CREATE TABLE IF NOT EXISTS statistics (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp INTEGER NOT NULL, type TEXT DEFAULT 'normal')")

        now = int(time.time())
        one_hour_ago = now - 3600
        one_week_ago = now - 7 * 24 * 3600

        cursor.execute("SELECT COUNT(*) FROM statistics WHERE timestamp > ?", (one_hour_ago,))
        last_hour = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM statistics WHERE timestamp > ?", (one_week_ago,))
        last_week = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM statistics")
        all_time = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM statistics WHERE timestamp > ? AND type IN ('violation_ad', 'violation_profanity')", (one_hour_ago,))
        violations_hour = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM statistics WHERE timestamp > ? AND type IN ('violation_ad', 'violation_profanity')", (one_week_ago,))
        violations_week = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM statistics WHERE type IN ('violation_ad', 'violation_profanity')")
        violations_all_time = cursor.fetchone()[0]

        conn.close()

        stats_message = (f"Статистика обработки сообщений:\n"
                         f"Последний час: {last_hour} (Нарушений: {violations_hour})\n"
                         f"Последняя неделя: {last_week} (Нарушений: {violations_week})\n"
                         f"Все время: {all_time} (Нарушений: {violations_all_time})")

        await callback.message.edit_text(stats_message)