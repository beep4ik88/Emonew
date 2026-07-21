import os
from google import genai

# Инициализируем клиент Gemini. 
# Ключ автоматически подтянется из переменной окружения GEMINI_API_KEY
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

async def generate_daily_summary(prompt: str) -> str:
    """
    Асинхронно отправляет промпт в Gemini и возвращает сгенерированный текст.
    """
    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"Ошибка при запросе к Gemini API: {e}")
        return "К сожалению, не удалось сгенерировать итоги дня. Попробуйте позже."
