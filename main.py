import asyncio
import logging
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Импорт вашей базы данных и модулей
import database as db
from handlers import start, emotion, feedback
from healthcheck import run_diagnostics, format_health_report, ADMIN_ID

# Настройка логирования в консоль
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

# Токен бота из переменных окружения Railway (или локального значения)
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_ЗДЕСЬ")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
main_router = Router()


# ==========================================
# 1. ОБРАБОТЧИКИ КОМАНД АДМИНИСТРАТОРА
# ==========================================

@main_router.message(Command("health"))
async def cmd_healthcheck(message: Message):
    """
    Ручной запуск самодиагностики по команде /health.
    Доступен ТОЛЬКО администратору с ID = ADMIN_ID.
    """
    if message.from_user.id != ADMIN_ID:
        return  # Простые пользователи игнорируются

    msg = await message.answer("🔄 Проводим диагностику систем...")

    # Запуск проверки через ваш модуль healthcheck.py
    report = await run_diagnostics(bot)
    report_text = format_health_report(report)

    await msg.edit_text(report_text, parse_mode="Markdown")


# ==========================================
# 2. ФОНОВЫЕ ЗАДАЧИ ПЛАНИРОВЩИКА (APSCHEDULER)
# ==========================================

async def hourly_tick():
    """
    Ежечасная задача: обход пользователей и отправка вопросов о самочувствии.
    """
    logging.info("⏰ Запуск ежечасного опроса пользователей (hourly_tick)...")
    
    try:
        if hasattr(db, 'get_all_users'):
            users = await db.get_all_users()
            for user in users:
                user_id = user.get('user_id') if isinstance(user, dict) else user[0]
                try:
                    # Безопасная отправка опроса
                    await bot.send_message(user_id, "Как ваше самочувствие? Выберите эмоцию.")
                except Exception as user_err:
                    logging.warning(f"Не удалось отправить опрос пользователю {user_id}: {user_err}")
    except Exception as e:
        logging.error(f"Ошибка при выполнении hourly_tick: {e}")


async def auto_health_check():
    """
    Шаг 3: Автоматическая фоновая самодиагностика.
    Запускается каждые 30 минут. Отправляет уведомление админу ТОЛЬКО в случае сбоя.
    """
    logging.info("🔍 Фоновый запуск автодиагностики...")
    
    report = await run_diagnostics(bot)
    
    # Проверяем, есть ли сбои хотя бы в одной системе
    db_ok = report.get("db", {}).get("status", False)
    tg_ok = report.get("telegram_api", {}).get("status", False)

    if not (db_ok and tg_ok):
        logging.error("🔴 Автодиагностика выявила проблемы в работе бота!")
        alert_text = "🚨 **ВНИМАНИЕ: Сбой в работе бота!**\n\n" + format_health_report(report)
        try:
            await bot.send_message(ADMIN_ID, alert_text, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление админу: {e}")


# ==========================================
# 3. ТОЧКА ВХОДА И ЗАПУСК БОТА
# ==========================================

async def main():
    # 1. Инициализация таблицы в БД при старте (если есть функция)
    if hasattr(db, 'init_db'):
        await db.init_db()

    # 2. Подключение роутеров
    dp.include_router(main_router)       # Главный роутер с /health
    dp.include_router(start.router)        # Команда /start и настройка времени
    dp.include_router(emotion.router)      # Опросы и выбор эмоций
    dp.include_router(feedback.router)     # Обратная связь

    # 3. Настройка и запуск планировщика задач APScheduler
    scheduler = AsyncIOScheduler()
    
    # Задача 1: Рассылка опросов каждый час ровно в 00 минут
    scheduler.add_job(hourly_tick, 'cron', minute=0)
    
    # Задача 2 (Шаг 3): Автоматическая проверка систем каждые 30 минут (в 15 и 45 минут каждого часа)
    scheduler.add_job(auto_health_check, 'cron', minute='15,45')
    
    scheduler.start()
    logging.info("🚀 APScheduler успешно запущен!")

    # 4. Сброс накопленных апдейтов и запуск Polling
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("🤖 Бот запущен и готов к работе.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")
