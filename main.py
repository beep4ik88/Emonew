import asyncio
import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

from config import BOT_TOKEN, ADMIN_ID
import database as db
from handlers import start, emotion, feedback
from scheduler import setup_scheduler
from healthcheck import run_diagnostics, format_health_report

logging.basicConfig(level=logging.INFO)

main_router = Router()


@main_router.message(Command("health"))
async def cmd_healthcheck(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    msg = await message.answer("🔄 Проводим диагностику систем...")
    report = await run_diagnostics(message.bot)
    await msg.edit_text(format_health_report(report))


async def auto_health_check(bot: Bot):
    report = await run_diagnostics(bot)
    db_ok = report["db"]["status"]
    tg_ok = report["telegram_api"]["status"]

    if not (db_ok and tg_ok):
        logging.error("Автодиагностика выявила проблемы в работе бота")
        alert_text = "🚨 Внимание: сбой в работе бота!\n\n" + format_health_report(report)
        try:
            await bot.send_message(ADMIN_ID, alert_text)
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление админу: {e}")


async def main():
    await db.init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(main_router)
    dp.include_router(start.router)
    dp.include_router(emotion.router)
    dp.include_router(feedback.router)

    scheduler = setup_scheduler(bot)
    scheduler.add_job(auto_health_check, "cron", minute="15,45", args=[bot])
    scheduler.start()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
