import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from config import BOT_TOKEN
import database as db
from handlers import start, emotion, feedback
from scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO)


# Функция для настройки меню (оставлены только /start и /feedback)
async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command="start", description="Настроить время / перезапуск"),
        BotCommand(command="feedback", description="Сообщить об ошибке или предложить идею"),
    ]
    await bot.set_my_commands(main_menu_commands)


async def main():
    await db.init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Устанавливаем кнопку меню
    await set_main_menu(bot)

    # Регистрируем роутеры
    dp.include_router(start.router)
    dp.include_router(emotion.router)
    dp.include_router(feedback.router)

    scheduler = setup_scheduler(bot)
    scheduler.start()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
