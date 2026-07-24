import logging
import httpx
from config import GEMINI_API_KEY

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent"
)

SYSTEM_PROMPT = (
    "Ты — внимательный психолог. Тебе присылают почасовой дневник эмоций одного человека "
    "за один день: время и выбранное состояние (базовая эмоция + один или несколько оттенков). "
    "Напиши анализ дня на русском языке, на 'вы', в свободной форме (без заголовков и списков), "
    "не длиннее 8-9 предложений:\n"
    "1) Динамика: как менялось состояние в течение дня — когда было лучше, когда хуже, "
    "заметен ли перелом или тенденция (например, ухудшение к вечеру, или наоборот). "
    "Опирайся только на реально переданные данные, не выдумывай причины, которых там нет.\n"
    "2) Если заметен повторяющийся паттерн (например, несколько раз за день похожие оттенки "
    "тревоги или раздражения) — отметь это отдельно.\n"
    "3) Дай 2 конкретные, выполнимые рекомендации: одну — на сегодняшний вечер, вторую — "
    "на завтра. Рекомендации должны быть привязаны к тому, что реально происходило в течение "
    "дня, а не общими фразами.\n"
    "Тон — тёплый, но сдержанный, без избыточной драматизации и без банальностей вроде "
    "'вы молодец' или 'берегите себя'."
)


async def generate_daily_summary(entries: list[tuple[str, str, str]], emotion_labels: dict) -> str | None:
    """Возвращает текст сводки, сгенерированный Gemini (бесплатный тариф),
    либо None, если ключ не настроен или запрос не удался (тогда вызывающий код
    должен использовать резервный шаблон). Причина сбоя всегда пишется в лог."""
    if not GEMINI_API_KEY:
        logging.warning("[llm] GEMINI_API_KEY не задан — используется шаблон")
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
            if response.status_code != 200:
                logging.error(
                    f"[llm] Gemini вернул статус {response.status_code}: {response.text[:500]}"
                )
                return None
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logging.error(f"[llm] Ошибка запроса к Gemini: {e}")
        return None


WEEKLY_SYSTEM_PROMPT = (
    "Ты — внимательный психолог. Тебе присылают дневник эмоций одного человека за последние "
    "7 дней: дата, время и выбранное состояние (базовая эмоция + оттенки). "
    "Напиши недельный анализ на русском языке, на 'вы', в свободной форме (без заголовков и "
    "списков), не длиннее 9-10 предложений:\n"
    "1) Как менялось состояние в течение недели — есть ли тренд (улучшение или ухудшение к "
    "концу недели), выделяются ли какие-то дни на фоне остальных.\n"
    "2) Какая эмоция или паттерн преобладали за неделю в целом.\n"
    "3) Если заметны повторяющиеся ситуации — отметь это.\n"
    "4) Дай 1-2 рекомендации на следующую неделю, привязанные к тому, что реально происходило.\n"
    "Опирайся только на переданные данные, не выдумывай причины, которых там нет. Тон тёплый, "
    "но сдержанный, без банальностей вроде 'вы молодец'."
)


async def generate_weekly_summary(
    entries: list[tuple[str, str, str, str]], emotion_labels: dict
) -> str | None:
    """entries: (primary_emotion, secondary_emotion, created_at, entry_date).
    Возвращает текст недельного анализа от Gemini, либо None при отсутствии ключа
    или сбое (тогда вызывающий код использует резервный шаблон)."""
    if not GEMINI_API_KEY:
        logging.warning("[llm] GEMINI_API_KEY не задан — недельная сводка по шаблону")
        return None

    lines = []
    for primary_key, secondary, created_at, entry_date in entries:
        time_part = created_at.split("T")[1][:5] if "T" in created_at else created_at
        label = emotion_labels.get(primary_key, primary_key)
        lines.append(f"{entry_date} {time_part} — {label}: {secondary}")
    entries_text = "\n".join(lines)

    payload = {
        "system_instruction": {"parts": [{"text": WEEKLY_SYSTEM_PROMPT}]},
        "contents": [
            {"role": "user", "parts": [{"text": f"Дневник эмоций за последние 7 дней:\n{entries_text}"}]}
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                GEMINI_URL,
                headers={"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"},
                json=payload,
            )
            if response.status_code != 200:
                logging.error(
                    f"[llm] Gemini (неделя) вернул статус {response.status_code}: {response.text[:500]}"
                )
                return None
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logging.error(f"[llm] Ошибка запроса к Gemini (неделя): {e}")
        return None
