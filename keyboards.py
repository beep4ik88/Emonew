from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from emotions import EMOTIONS, EMOTION_ORDER


def primary_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=EMOTIONS[key]["label"], callback_data=f"p:{key}")]
        for key in EMOTION_ORDER
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def secondary_keyboard(primary_key: str, selected: set[int] | None = None) -> InlineKeyboardMarkup:
    """Множественный выбор уточнений: отмеченные помечаются галочкой.
    callback_data кодируется как индекс в списке (иначе можно превысить
    лимит Telegram в 64 байта), раскладка — по 2 кнопки в ряд."""
    selected = selected or set()
    options = EMOTIONS[primary_key]["secondary"]
    buttons = []
    row = []
    for idx, opt in enumerate(options):
        text = f"✅ {opt}" if idx in selected else opt
        row.append(InlineKeyboardButton(text=text, callback_data=f"t:{primary_key}:{idx}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="✅ Готово", callback_data=f"done:{primary_key}")])
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


def extra_count_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=str(n), callback_data=f"extra_count:{n}") for n in [0, 1, 2, 3]]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def extra_hour_keyboard() -> InlineKeyboardMarkup:
    hours = list(range(9, 22))  # 9:00-21:00
    buttons = []
    row = []
    for h in hours:
        row.append(InlineKeyboardButton(text=f"{h}:00", callback_data=f"extra_hour:{h}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)
