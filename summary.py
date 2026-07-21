from collections import Counter
from emotions import EMOTIONS
from llm import generate_daily_summary

RECOMMENDATIONS = {
    "anger": (
        "Гнев сегодня был заметным гостем. Это нормальная реакция на нарушенные границы "
        "или несправедливость. Попробуйте сегодня перед сном выписать на бумагу, что именно "
        "вызвало раздражение — часто становится легче, когда эмоция превращается в слова."
    ),
    "fear": (
        "День прошёл с ощутимой тревогой. Тело в такие дни держит мышцы в напряжении дольше, "
        "чем мы замечаем. Попробуйте перед сном 5 минут медленного дыхания: вдох на 4 счёта, "
        "выдох на 6 — это снижает уровень тревожной активации."
    ),
    "sadness": (
        "Сегодня преобладала грусть. Это не всегда плохой знак — иногда это сигнал, что нужно "
        "замедлиться и позаботиться о себе. Разрешите себе сегодня лечь чуть раньше и без "
        "самокритики за уставший день."
    ),
    "joy": (
        "День был наполнен радостью — отличный повод отметить, что сегодня получилось, и "
        "вернуться к этому воспоминанию, когда будет сложнее. Полезно записать 1-2 момента, "
        "которые особенно порадовали."
    ),
    "love": (
        "Сегодня преобладало тепло и близость с кем-то. Это ценный ресурс — стоит заметить, "
        "с кем или с чем это было связано, чтобы осознанно возвращаться к этим источникам."
    ),
}

NEUTRAL_RECOMMENDATION = (
    "Сегодня не было явно доминирующей эмоции — эмоциональный фон был смешанным. "
    "Это тоже нормально: не каждый день укладывается в одно состояние."
)


def _stats_block(entries: list[tuple[str, str, str]]) -> str:
    primary_counts = Counter(e[0] for e in entries)
    total = len(entries)
    lines = ["📊 Сводка дня\n"]
    for key in ["anger", "fear", "sadness", "joy", "love"]:
        count = primary_counts.get(key, 0)
        if count:
            share = round(100 * count / total)
            lines.append(f"{EMOTIONS[key]['label']}: {count} раз ({share}%)")
    return "\n".join(lines)


def _template_recommendation(entries: list[tuple[str, str, str]]) -> str:
    primary_counts = Counter(e[0] for e in entries)
    total = len(entries)
    dominant, dominant_count = primary_counts.most_common(1)[0]
    if dominant_count / total >= 0.4:
        return RECOMMENDATIONS[dominant]
    return NEUTRAL_RECOMMENDATION


async def build_daily_summary(entries: list[tuple[str, str, str]]) -> str:
    """
    entries: список кортежей (primary_emotion, secondary_emotion, created_at)
    Сначала пробует сгенерировать текст через Claude API; если ключ не настроен
    или запрос не удался — использует резервный шаблон.
    """
    if not entries:
        return (
            "Сегодня не было ни одной отметки — возможно, день выдался занятым. "
            "Ничего страшного, завтра начнём заново."
        )

    stats = _stats_block(entries)
    emotion_labels = {key: EMOTIONS[key]["label"] for key in EMOTIONS}

    llm_text = await generate_daily_summary(entries, emotion_labels)
    recommendation = llm_text if llm_text else _template_recommendation(entries)

    return f"{stats}\n\n{recommendation}"
