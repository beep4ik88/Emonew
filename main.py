import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
import database as db
# 👇 Подключаем новый модуль feedback вместе с остальными
from handlers import start, emotion, feedback
from scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO)


async def main():
    await db.init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    # Регистрируем все роутеры бота
    dp.include_router(start.router)
    dp.include_router(emotion.router)
    dp.include_router(feedback.router)  # 👈 Добавили обработчик обратной связи

    scheduler = setup_scheduler(bot)
    scheduler.start()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
