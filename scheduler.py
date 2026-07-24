import logging
from datetime import date, datetime, timedelta
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

import database as db
import keyboards as kb
from summary import build_daily_summary, build_weekly_summary


async def hourly_tick(bot: Bot):
    """Запускается каждый час; для каждого пользователя проверяет, попадает ли
    текущий час (в его таймзоне) в его окно бодрствования, и либо шлёт вопрос,
    либо (если это час отбоя) шлёт вопрос + сводку дня, а по воскресеньям — ещё
    и сводку недели."""
    users = await db.get_all_onboarded_users()
    logging.info(f"[hourly_tick] найдено пользователей: {len(users)}")

    for user_id, wake_hour, sleep_hour, timezone in users:
        tz = pytz.timezone(timezone or "Europe/Moscow")
        now_local = datetime.now(tz)
        current_hour = now_local.hour

        logging.info(
            f"[hourly_tick] user={user_id} wake={wake_hour} sleep={sleep_hour} "
            f"tz={timezone} current_local_hour={current_hour}"
        )

        if current_hour == sleep_hour:
            try:
                await bot.send_message(
                    user_id,
                    "Что вы сейчас чувствуете?",
                    reply_markup=kb.primary_keyboard(),
                )
                logging.info(f"[hourly_tick] user={user_id} -> последний вопрос дня отправлен")
            except Exception as e:
                logging.error(f"[hourly_tick] user={user_id} -> ошибка отправки последнего вопроса: {e}")

            today_str = date.today().isoformat()
            entries = await db.get_entries_for_date(user_id, today_str)
            text = await build_daily_summary(entries)
            try:
                await bot.send_message(user_id, text)
                logging.info(f"[hourly_tick] user={user_id} -> отправлена сводка дня")
            except Exception as e:
                logging.error(f"[hourly_tick] user={user_id} -> ошибка отправки сводки: {e}")

            # По воскресеньям (в локальном времени пользователя) — ещё и недельная сводка
            if now_local.weekday() == 6:
                week_start = (now_local.date() - timedelta(days=6)).isoformat()
                week_end = now_local.date().isoformat()
                week_entries = await db.get_entries_for_range(user_id, week_start, week_end)
                weekly_text = await build_weekly_summary(week_entries)
                try:
                    await bot.send_message(user_id, weekly_text)
                    logging.info(f"[hourly_tick] user={user_id} -> отправлена недельная сводка")
                except Exception as e:
                    logging.error(f"[hourly_tick] user={user_id} -> ошибка отправки недельной сводки: {e}")

            continue

        in_window = (
            wake_hour <= current_hour < sleep_hour
            if wake_hour < sleep_hour
            else (current_hour >= wake_hour or current_hour < sleep_hour)
        )
        logging.info(f"[hourly_tick] user={user_id} in_window={in_window}")

        if in_window:
            try:
                await bot.send_message(
                    user_id,
                    "Что вы сейчас чувствуете?",
                    reply_markup=kb.primary_keyboard(),
                )
                logging.info(f"[hourly_tick] user={user_id} -> вопрос отправлен")
            except Exception as e:
                logging.error(f"[hourly_tick] user={user_id} -> ошибка отправки вопроса: {e}")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(hourly_tick, "cron", minute=0, args=[bot])
    return scheduler
