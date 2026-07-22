import asyncpg
from datetime import datetime
from config import DATABASE_URL

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    wake_hour INTEGER,
    sleep_hour INTEGER,
    timezone TEXT DEFAULT 'Europe/Moscow',
    onboarded INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS entries (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    entry_date TEXT,
    primary_emotion TEXT,
    secondary_emotion TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS pending (
    user_id BIGINT PRIMARY KEY,
    primary_emotion TEXT,
    message_id BIGINT
);
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


async def upsert_user(user_id: int, wake_hour: int, sleep_hour: int, timezone: str = "Europe/Moscow"):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO users (user_id, wake_hour, sleep_hour, timezone, onboarded)
               VALUES ($1, $2, $3, $4, 1)
               ON CONFLICT (user_id) DO UPDATE SET
                 wake_hour=EXCLUDED.wake_hour,
                 sleep_hour=EXCLUDED.sleep_hour,
                 timezone=EXCLUDED.timezone,
                 onboarded=1""",
            user_id, wake_hour, sleep_hour, timezone,
        )


async def get_all_onboarded_users():
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT user_id, wake_hour, sleep_hour, timezone FROM users WHERE onboarded=1"
        )
        return [(r["user_id"], r["wake_hour"], r["sleep_hour"], r["timezone"]) for r in rows]


async def get_user(user_id: int):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT user_id, wake_hour, sleep_hour, timezone FROM users WHERE user_id=$1",
            user_id,
        )
        return (row["user_id"], row["wake_hour"], row["sleep_hour"], row["timezone"]) if row else None


async def set_pending(user_id: int, primary_emotion: str, message_id: int):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO pending (user_id, primary_emotion, message_id)
               VALUES ($1, $2, $3)
               ON CONFLICT (user_id) DO UPDATE SET
                 primary_emotion=EXCLUDED.primary_emotion,
                 message_id=EXCLUDED.message_id""",
            user_id, primary_emotion, message_id,
        )


async def pop_pending(user_id: int):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT primary_emotion, message_id FROM pending WHERE user_id=$1", user_id
        )
        await conn.execute("DELETE FROM pending WHERE user_id=$1", user_id)
        return (row["primary_emotion"], row["message_id"]) if row else None


async def save_entry(user_id: int, primary_emotion: str, secondary_emotion: str, entry_date: str):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO entries (user_id, entry_date, primary_emotion, secondary_emotion, created_at)
               VALUES ($1, $2, $3, $4, $5)""",
            user_id, entry_date, primary_emotion, secondary_emotion, datetime.now().isoformat(),
        )


async def get_entries_for_date(user_id: int, entry_date: str):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT primary_emotion, secondary_emotion, created_at FROM entries
               WHERE user_id=$1 AND entry_date=$2 ORDER BY created_at""",
            user_id, entry_date,
        )
        return [(r["primary_emotion"], r["secondary_emotion"], r["created_at"]) for r in rows]
