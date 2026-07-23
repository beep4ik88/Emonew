from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from emotions import EMOTIONS, EMOTION_ORDER


def primary_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=EMOTIONS[key]["label"], callback_data=f"p:{key}")]
        for key in EMOTION_ORDER
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def secondary_keyboard(primary_key: str) -> InlineKeyboardMarkup:
    """Списки уточнений длинные (20-30 слов), поэтому callback_data кодируется
    как индекс в списке (иначе можно превысить лимит Telegram в 64 байта),
    а раскладка — по 2 кнопки в ряд, чтобы список поместился компактнее."""
    options = EMOTIONS[primary_key]["secondary"]
    buttons = []
    row = []
    for idx, opt in enumerate(options):
        row.append(InlineKeyboardButton(text=opt, callback_data=f"s:{primary_key}:{idx}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_primary")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def wake_hour_keyboard() -> InlineKeyboardMarkup:
    hours = [6, 7, 8, 9, 10]
    buttons = [[InlineKeyboardButton(text=f"{h}:00", callback_data=f"wake:{h}") for h in hours]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def sleep_hour_keyboard() -> InlineKeyboardMarkup:
    hours = [21, 22, 23, 0, 1]
    buttons = [[InlineKeyboardButton(text=f"{h}:00", callback_data=f"sleep:{h}") for h in hours]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
