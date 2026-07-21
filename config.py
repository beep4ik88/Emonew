import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден. Создайте файл .env на основе .env.example")

DB_PATH = os.getenv("DB_PATH", "emotoday.db")
DEFAULT_TZ = os.getenv("DEFAULT_TZ", "Europe/Moscow")

# Ключ от Google Gemini (для ИИ-сводки дня)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Telegram ID администратора для фидбека и ошибок
ADMIN_ID = int(os.getenv("ADMIN_ID", 391863566))
