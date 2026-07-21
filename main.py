import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Импорт вашей базы данных и хэндлеров
import database as db
from handlers import start, emotion, feedback
from healthcheck import run_diagnostics, format_health_report, ADMIN_ID

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Получение токена из переменных окружения (Railway / .env)
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_ЕСЛИ_ЛОКАЛЬНО")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
main_router = Router()


# --- 1. Обработчик команды диагностики /health (Только для админа) ---
@main_router.message(Command("health"))
async def cmd_healthcheck(message: Message):
    # Если пишет не админ — просто игнорируем
    if message.from_user.id != ADMIN_ID:
        return

    msg = await message.answer("🔄 Проводим диагностику систем...")

    # Запуск диагностики
    report = await run_diagnostics(bot)
    report_text = format_health_report(report)

    await msg.edit_text(report_text, parse_mode="Markdown")


# --- 2. Фоновые задачи (APScheduler) ---
async def hourly_tick():
    """Каждый час отправляет опросы активным пользователям"""
    logging.info("Выполнение планового опроса (hourly_tick)...")
    # Ваша логика обхода пользователей и рассылки


async def auto_health_check():
    """Фоновая автоматическая самодиагностика"""
    report = await run_diagnostics(bot)
    
    # Если БД или Telegram API дали сбой — отправляем экстренный сигнал админу
    if not (report["db"]["status"] and report["telegram_api"]["status"]):
        alert_text = "🚨 **ВНИМАНИЕ: Сбой в работе бота!**\n\n" + format_health_report(report)
        try:
            await bot.send_message(ADMIN_ID, alert_text, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление админу: {e}")


# --- 3. Точка входа и запуск бота ---
async def main():
    # Инициализируем БД при старте (если есть функция инициализации)
    if hasattr(db, 'init_db'):
        await db.init_db()

    # Регистрация всех роутеров в Dispatcher
    dp.include_router(main_router)       # Главный роутер с /health
    dp.include_router(start.router)        # Хэндлеры команды /start и настройки времени
    dp.include_router(emotion.router)      # Хэндлеры опросов и выбора эмоций
    dp.include_router(feedback.router)     # Хэндлеры обратной связи

    # Настройка и запуск планировщика задач
    scheduler = AsyncIOScheduler()
    # Ежечасный опрос ровно в 00 минут каждого часа
    scheduler.add_job(hourly_tick, 'cron', minute=0)
    # Автодиагностика каждый час в 30 минут
    scheduler.add_job(auto_health_check, 'cron', minute=30)
    
    scheduler.start()

    logging.info("🚀 Бот и планировщик успешно запущены!")

    # Удаляем накопившиеся апдейты и запускаем Polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
