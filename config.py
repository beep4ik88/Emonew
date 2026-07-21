import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден. Создайте файл .env на основе .env.example")

DB_PATH = os.getenv("DB_PATH", "emotoday.db")
DEFAULT_TZ = os.getenv("DEFAULT_TZ", "Europe/Moscow")

# Опционально: если не задан, сводка дня будет собираться по шаблону (без вызова LLM)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
