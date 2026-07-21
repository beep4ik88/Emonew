from datetime import date, datetime
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

import database as db
import keyboards as kb
from summary import build_daily_summary


async def hourly_tick(bot: Bot):
    """Запускается каждый час; для каждого пользователя проверяет, попадает ли
    текущий час (в его таймзоне) в его окно бодрствования, и либо шлёт вопрос,
    либо (если это час отбоя) шлёт сводку дня."""
    users = await db.get_all_onboarded_users()
    for user_id, wake_hour, sleep_hour, timezone in users:
        tz = pytz.timezone(timezone or "Europe/Moscow")
        now_local = datetime.now(tz)
        current_hour = now_local.hour

        if current_hour == sleep_hour:
            entries = await db.get_entries_for_date(user_id, date.today().isoformat())
            text = await build_daily_summary(entries)
            await bot.send_message(user_id, text)
            continue

        in_window = (
            wake_hour <= current_hour < sleep_hour
            if wake_hour < sleep_hour
            else (current_hour >= wake_hour or current_hour < sleep_hour)
        )
        if in_window:
            await bot.send_message(
                user_id,
                "Что вы сейчас чувствуете?",
                reply_markup=kb.primary_keyboard(),
            )


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(hourly_tick, "cron", minute=0, args=[bot])
    return scheduler
