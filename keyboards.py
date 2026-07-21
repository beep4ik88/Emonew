from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==================== КЛАВИАТУРЫ ДЛЯ /start ====================

def wake_hour_keyboard() -> InlineKeyboardMarkup:
    """Выбор часа пробуждения (06:00 - 11:00)"""
    buttons = []
    for h in range(6, 12):
        buttons.append([InlineKeyboardButton(text=f"{h:02d}:00", callback_data=f"set_wake:{h}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def sleep_hour_keyboard() -> InlineKeyboardMarkup:
    """Выбор часа сна (21:00 - 02:00)"""
    hours = [21, 22, 23, 0, 1, 2]
    buttons = []
    for h in hours:
        buttons.append([InlineKeyboardButton(text=f"{h:02d}:00", callback_data=f"set_sleep:{h}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def timezone_keyboard() -> InlineKeyboardMarkup:
    """Выбор часового пояса"""
    buttons = [
        [InlineKeyboardButton(text="Московское время (UTC+3)", callback_data="set_tz:Europe/Moscow")],
        [InlineKeyboardButton(text="Калининград (UTC+2)", callback_data="set_tz:Europe/Kaliningrad")],
        [InlineKeyboardButton(text="Екатеринбург (UTC+5)", callback_data="set_tz:Asia/Yekaterinburg")],
        [InlineKeyboardButton(text="Новосибирск (UTC+7)", callback_data="set_tz:Asia/Novosibirsk")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ==================== КЛАВИАТУРЫ ДЛЯ ЭМОЦИЙ ====================

# 1. Шаг 1: Категории
def primary_emotion_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="😁 Отличное", callback_data="emo_cat:great")],
        [InlineKeyboardButton(text="🙂 Хорошее", callback_data="emo_cat:good")],
        [InlineKeyboardButton(text="😐 Нейтральное", callback_data="emo_cat:neutral")],
        [InlineKeyboardButton(text="🙁 Плохое", callback_data="emo_cat:bad")],
        [InlineKeyboardButton(text="😫 Ужасное", callback_data="emo_cat:terrible")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Список уточняющих оттенков
SUB_EMOTIONS = [
    "Энергия ⚡", "Спокойствие 🧘", "Радость 😊", 
    "Усталость 🥱", "Тревога 😰", "Раздражение 😡", 
    "Грусть 😢", "Фокус 🎯"
]

# 2. Шаг 2: Мультивыбор с галочками
def sub_emotion_keyboard(selected_items: list[str]) -> InlineKeyboardMarkup:
    buttons = []
    for item in SUB_EMOTIONS:
        is_selected = item in selected_items
        prefix = "✅ " if is_selected else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"{prefix}{item}", 
                callback_data=f"toggle_emo:{item}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="✨ Готово", callback_data="finish_emo_selection")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
