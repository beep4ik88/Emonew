import httpx
from config import GEMINI_API_KEY

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent"
)

SYSTEM_PROMPT = (
    "Ты — внимательный психолог. Тебе присылают почасовой дневник эмоций одного человека "
    "за один день: время и выбранное состояние (базовая эмоция + уточнение). "
    "Напиши короткую сводку дня на русском языке, на 'вы': "
    "1) что было заметно в динамике состояния за день (2-3 предложения, по существу, без клише "
    "и без выдуманных подробностей о том, что не сказано в данных); "
    "2) 1-2 конкретные, выполнимые рекомендации на вечер или на завтра. "
    "Тон — тёплый, но сдержанный, без избыточной драматизации и без банальностей "
    "вроде 'вы молодец'. Общий объём — не больше 6-7 предложений."
)


async def generate_daily_summary(entries: list[tuple[str, str, str]], emotion_labels: dict) -> str | None:
    """Возвращает текст сводки, сгенерированный Gemini (бесплатный тариф),
    либо None, если ключ не настроен или запрос не удался (тогда вызывающий код
    должен использовать резервный шаблон)."""
    if not GEMINI_API_KEY:
        return None

    lines = []
    for primary_key, secondary, created_at in entries:
        time_part = created_at.split("T")[1][:5] if "T" in created_at else created_at
        label = emotion_labels.get(primary_key, primary_key)
        lines.append(f"{time_part} — {label}: {secondary}")
    entries_text = "\n".join(lines)

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [
            {"role": "user", "parts": [{"text": f"Дневник эмоций за сегодня:\n{entries_text}"}]}
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                GEMINI_URL,
                headers={"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return None
