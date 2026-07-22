import aiosqlite
from datetime import datetime
from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    wake_hour INTEGER,
    sleep_hour INTEGER,
    timezone TEXT DEFAULT 'Europe/Moscow',
    onboarded INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    entry_date TEXT,
    primary_emotion TEXT,
    secondary_emotion TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS pending (
    user_id INTEGER PRIMARY KEY,
    primary_emotion TEXT,
    message_id INTEGER
);
"""


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def upsert_user(user_id: int, wake_hour: int, sleep_hour: int, timezone: str = "Europe/Moscow"):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO users (user_id, wake_hour, sleep_hour, timezone, onboarded)
               VALUES (?, ?, ?, ?, 1)
               ON CONFLICT(user_id) DO UPDATE SET
                 wake_hour=excluded.wake_hour,
                 sleep_hour=excluded.sleep_hour,
                 timezone=excluded.timezone,
                 onboarded=1""",
            (user_id, wake_hour, sleep_hour, timezone),
        )
        await db.commit()


async def get_all_onboarded_users():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT user_id, wake_hour, sleep_hour, timezone FROM users WHERE onboarded=1"
        )
        return await cursor.fetchall()


async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT user_id, wake_hour, sleep_hour, timezone FROM users WHERE user_id=?",
            (user_id,),
        )
        return await cursor.fetchone()


async def set_pending(user_id: int, primary_emotion: str, message_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO pending (user_id, primary_emotion, message_id)
               VALUES (?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                 primary_emotion=excluded.primary_emotion,
                 message_id=excluded.message_id""",
            (user_id, primary_emotion, message_id),
        )
        await db.commit()


async def pop_pending(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT primary_emotion, message_id FROM pending WHERE user_id=?", (user_id,)
        )
        row = await cursor.fetchone()
        await db.execute("DELETE FROM pending WHERE user_id=?", (user_id,))
        await db.commit()
        return row


async def save_entry(user_id: int, primary_emotion: str, secondary_emotion: str, entry_date: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO entries (user_id, entry_date, primary_emotion, secondary_emotion, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, entry_date, primary_emotion, secondary_emotion, datetime.now().isoformat()),
        )
        await db.commit()


async def get_entries_for_date(user_id: int, entry_date: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT primary_emotion, secondary_emotion, created_at FROM entries
               WHERE user_id=? AND entry_date=? ORDER BY created_at""",
            (user_id, entry_date),
        )
        return await cursor.fetchall()
