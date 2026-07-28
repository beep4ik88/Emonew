import asyncpg
from datetime import datetime
from config import DATABASE_URL

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    wake_hour INTEGER,
    sleep_hour INTEGER,
    extra_hours TEXT DEFAULT '',
    timezone TEXT DEFAULT 'Europe/Moscow',
    onboarded INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS entries (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    entry_date TEXT,
    primary_emotion TEXT,
    secondary_emotion TEXT,
    body_sensation TEXT,
    created_at TEXT
);

ALTER TABLE users ADD COLUMN IF NOT EXISTS extra_hours TEXT DEFAULT '';
ALTER TABLE entries ADD COLUMN IF NOT EXISTS body_sensation TEXT;
"""

_pool: asyncpg.Pool | None = None


async def _get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL)
    return _pool


async def init_db():
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(SCHEMA)


async def upsert_user(
    user_id: int,
    wake_hour: int,
    sleep_hour: int,
    extra_hours: str = "",
    timezone: str = "Europe/Moscow",
):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO users (user_id, wake_hour, sleep_hour, extra_hours, timezone, onboarded)
               VALUES ($1, $2, $3, $4, $5, 1)
               ON CONFLICT (user_id) DO UPDATE SET
                 wake_hour=EXCLUDED.wake_hour,
                 sleep_hour=EXCLUDED.sleep_hour,
                 extra_hours=EXCLUDED.extra_hours,
                 timezone=EXCLUDED.timezone,
                 onboarded=1""",
            user_id, wake_hour, sleep_hour, extra_hours, timezone,
        )


async def get_all_onboarded_users():
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT user_id, wake_hour, sleep_hour, extra_hours, timezone FROM users WHERE onboarded=1"
        )
        return [
            (r["user_id"], r["wake_hour"], r["sleep_hour"], r["extra_hours"], r["timezone"])
            for r in rows
        ]


async def get_user(user_id: int):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT user_id, wake_hour, sleep_hour, extra_hours, timezone FROM users WHERE user_id=$1",
            user_id,
        )
        if not row:
            return None
        return (row["user_id"], row["wake_hour"], row["sleep_hour"], row["extra_hours"], row["timezone"])


async def save_entry(
    user_id: int,
    primary_emotion: str,
    secondary_emotion: str,
    entry_date: str,
    body_sensation: str = "",
):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO entries (user_id, entry_date, primary_emotion, secondary_emotion, body_sensation, created_at)
               VALUES ($1, $2, $3, $4, $5, $6)""",
            user_id, entry_date, primary_emotion, secondary_emotion, body_sensation, datetime.now().isoformat(),
        )


async def get_entries_for_date(user_id: int, entry_date: str):
    """Возвращает (primary_emotion, secondary_emotion, created_at, body_sensation)."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT primary_emotion, secondary_emotion, created_at, body_sensation FROM entries
               WHERE user_id=$1 AND entry_date=$2 ORDER BY created_at""",
            user_id, entry_date,
        )
        return [
            (r["primary_emotion"], r["secondary_emotion"], r["created_at"], r["body_sensation"])
            for r in rows
        ]


async def get_entries_for_range(user_id: int, start_date: str, end_date: str):
    """Записи за диапазон дат включительно (ISO-строки YYYY-MM-DD).
    Возвращает (primary_emotion, secondary_emotion, created_at, entry_date, body_sensation)."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT primary_emotion, secondary_emotion, created_at, entry_date, body_sensation FROM entries
               WHERE user_id=$1 AND entry_date >= $2 AND entry_date <= $3 ORDER BY entry_date, created_at""",
            user_id, start_date, end_date,
        )
        return [
            (r["primary_emotion"], r["secondary_emotion"], r["created_at"], r["entry_date"], r["body_sensation"])
            for r in rows
        ]
