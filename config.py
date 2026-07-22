import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден. Создайте файл .env на основе .env.example")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL не найден. Добавьте сервис Postgres в Railway и подключите его переменную."
    )
DEFAULT_TZ = os.getenv("DEFAULT_TZ", "Europe/Moscow")

# Опционально: если не задан, сводка дня будет собираться по шаблону (без вызова LLM)
# Бесплатный ключ: aistudio.google.com
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Ваш личный Telegram ID — получает уведомления о сбоях и обратную связь от пользователей
ADMIN_ID = int(os.getenv("ADMIN_ID", "391863566"))
