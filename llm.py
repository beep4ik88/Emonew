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


async def generate_daily_summary(entries: list[tuple[str, str, str, str]], emotion_labels: dict) -> str | None:
    """Возвращает текст сводки, сгенерированный Gemini (бесплатный тариф),
    либо None, если ключ не настроен или запрос не удался (тогда вызывающий код
    должен использовать резервный шаблон). Причина сбоя всегда пишется в лог."""
    if not GEMINI_API_KEY:
        logging.warning("[llm] GEMINI_API_KEY не задан — используется шаблон")
        return None

    lines = []
    for primary_key, secondary, created_at, body in entries:
        time_part = created_at.split("T")[1][:5] if "T" in created_at else created_at
        label = emotion_labels.get(primary_key, primary_key)
        line = f"{time_part} — {label}: {secondary}"
        if body:
            line += f" (тело: {body})"
        lines.append(line)
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
    entries: list[tuple[str, str, str, str, str]], emotion_labels: dict
) -> str | None:
    """entries: (primary_emotion, secondary_emotion, created_at, entry_date, body_sensation).
    Возвращает текст недельного анализа от Gemini, либо None при отсутствии ключа
    или сбое (тогда вызывающий код использует резервный шаблон)."""
    if not GEMINI_API_KEY:
        logging.warning("[llm] GEMINI_API_KEY не задан — недельная сводка по шаблону")
        return None

    lines = []
    for primary_key, secondary, created_at, entry_date, body in entries:
        time_part = created_at.split("T")[1][:5] if "T" in created_at else created_at
        label = emotion_labels.get(primary_key, primary_key)
        line = f"{entry_date} {time_part} — {label}: {secondary}"
        if body:
            line += f" (тело: {body})"
        lines.append(line)
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


TECHNIQUE_SYSTEM_PROMPT = (
    "Ты — специалист по телесно-ориентированной саморегуляции, работаешь по методу дневника "
    "эмоций на основе колеса Плутчика. Пользователь сообщает: какую базовую эмоцию и оттенки "
    "он сейчас переживает, и как это ощущается в теле. Дай короткий практичный совет на "
    "русском языке, на 'вы', без заголовков и списков, 3-5 предложений: конкретную телесную "
    "технику, которая поможет именно с этой эмоцией и с этими ощущениями (например, для гнева "
    "— сброс мышечного напряжения: активные движения, поколотить подушку, порвать бумагу; для "
    "страха — заземление и медленное дыхание; для грусти — тепло и разрешение себе замедлиться; "
    "для отвращения — физическое дистанцирование; и так далее по каждой эмоции). Завершите "
    "одним коротким рефлексивным вопросом в духе «где ещё в жизни у вас случается похожее и "
    "как вы могли бы на это влиять» — не растягивайте, максимум одно предложение. Тон тёплый "
    "и практичный, без клише."
)

TECHNIQUE_FALLBACKS = {
    "anger": (
        "Похоже на телесное напряжение, которое ищет выход. Попробуйте активно поработать "
        "мышцами: 5-7 минут быстрой ходьбы по лестнице, несколько ударов по подушке или "
        "порвите лист бумаги — это помогает сбросить накопившееся напряжение."
    ),
    "fear": (
        "Тело в тревоге часто застывает. Попробуйте заземлиться: назовите вслух 5 предметов, "
        "которые видите, и сделайте несколько медленных вдохов на 4 счёта и выдохов на 6."
    ),
    "sadness": (
        "Грусти иногда нужно просто дать место. Найдите тёплое одеяло, сделайте тёплый напиток "
        "и разрешите себе не быть продуктивными ближайшие 15 минут."
    ),
    "joy": (
        "Радость стоит закрепить в теле — потянитесь, улыбнитесь чуть шире, сделайте несколько "
        "глубоких свободных вдохов, чтобы это состояние отпечаталось в памяти."
    ),
    "trust": (
        "Доверие — хорошая опора. Обратите внимание, где в теле вы чувствуете эту устойчивость, "
        "и на пару секунд задержитесь на этом ощущении."
    ),
    "disgust": (
        "Отвращение — сигнал границы. Попробуйте физически отстраниться: встать, отойти, "
        "вымыть руки — это помогает телу завершить реакцию."
    ),
    "surprise": (
        "После неожиданности телу нужно немного времени, чтобы прийти в себя. Постойте "
        "спокойно несколько секунд и сделайте один глубокий вдох-выдох, прежде чем действовать."
    ),
    "anticipation": (
        "Ожидание держит тело в лёгком напряжении. Попробуйте назвать вслух, чего именно вы "
        "ждёте — это снижает фоновую тревожность предвкушения."
    ),
}


async def generate_technique(primary_label: str, secondary_text: str, body_text: str) -> str | None:
    """Возвращает технику самопомощи от Gemini под конкретную эмоцию и телесный отклик,
    либо None при отсутствии ключа/сбое — тогда используется TECHNIQUE_FALLBACKS."""
    if not GEMINI_API_KEY:
        logging.warning("[llm] GEMINI_API_KEY не задан — техника по шаблону")
        return None

    user_message = (
        f"Эмоция: {primary_label}\nОттенки: {secondary_text}\nТелесные ощущения: {body_text}"
    )

    payload = {
        "system_instruction": {"parts": [{"text": TECHNIQUE_SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": user_message}]}],
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
                    f"[llm] Gemini (техника) вернул статус {response.status_code}: {response.text[:500]}"
                )
                return None
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logging.error(f"[llm] Ошибка запроса к Gemini (техника): {e}")
        return None
