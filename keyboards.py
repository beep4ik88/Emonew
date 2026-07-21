from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def wake_hour_keyboard() -> InlineKeyboardMarkup:
    """Выбор часа подъема"""
    buttons = []
    for h in range(6, 12):
        buttons.append([InlineKeyboardButton(text=f"{h:02d}:00", callback_data=f"set_wake:{h}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def sleep_hour_keyboard() -> InlineKeyboardMarkup:
    """Выбор часа сна"""
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
