from datetime import datetime
import aiosqlite
from aiogram import Bot

from config import DB_PATH


async def run_diagnostics(bot: Bot) -> dict:
    """Проводит диагностику базы данных и связи с Telegram API."""
    results = {
        "db": {"status": False, "details": ""},
        "telegram_api": {"status": False, "details": ""},
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    try:
        async with aiosqlite.connect(DB_PATH) as db_conn:
            async with db_conn.execute("SELECT 1") as cursor:
                res = await cursor.fetchone()
                if res and res[0] == 1:
                    results["db"]["status"] = True
                    results["db"]["details"] = "Подключение и чтение OK"
    except Exception as e:
        results["db"]["details"] = f"Ошибка БД: {e}"

    try:
        me = await bot.get_me()
        results["telegram_api"]["status"] = True
        results["telegram_api"]["details"] = f"OK (@{me.username})"
    except Exception as e:
        results["telegram_api"]["details"] = f"Ошибка Telegram API: {e}"

    return results


def format_health_report(report: dict) -> str:
    """Форматирует результат диагностики в текст для Telegram."""
    db_icon = "✅" if report["db"]["status"] else "❌"
    tg_icon = "✅" if report["telegram_api"]["status"] else "❌"

    all_ok = report["db"]["status"] and report["telegram_api"]["status"]
    status_summary = "🟢 Системы работают штатно" if all_ok else "🔴 Обнаружены проблемы!"

    return (
        f"🏥 Отчёт самодиагностики\n"
        f"⏱ Время: {report['timestamp']}\n\n"
        f"Статус: {status_summary}\n\n"
        f"{db_icon} База данных: {report['db']['details']}\n"
        f"{tg_icon} Telegram API: {report['telegram_api']['details']}\n"
    )
