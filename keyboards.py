from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# 1. Первый шаг: 5 базовых настроений
def primary_emotion_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="😁 Отличное", callback_data="emo_cat:great")],
        [InlineKeyboardButton(text="🙂 Хорошее", callback_data="emo_cat:good")],
        [InlineKeyboardButton(text="😐 Нейтральное", callback_data="emo_cat:neutral")],
        [InlineKeyboardButton(text="🙁 Плохое", callback_data="emo_cat:bad")],
        [InlineKeyboardButton(text="😫 Ужасное", callback_data="emo_cat:terrible")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Список уточняющих эмоций/оттенков (можно дополнить своими)
SUB_EMOTIONS = [
    "Энергия ⚡", "Спокойствие 🧘", "Радость 😊", 
    "Усталость 🥱", "Тревога 😰", "Раздражение 😡", 
    "Грусть 😢", "Фокус 🎯"
]

# 2. Второй шаг: Мультивыбор с галочками
def sub_emotion_keyboard(selected_items: list[str]) -> InlineKeyboardMarkup:
    buttons = []
    
    # Создаем кнопки с галочками для выбранных элементов
    for item in SUB_EMOTIONS:
        is_selected = item in selected_items
        prefix = "✅ " if is_selected else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"{prefix}{item}", 
                callback_data=f"toggle_emo:{item}"
            )
        ])
    
    # Кнопка завершения выбора
    buttons.append([
        InlineKeyboardButton(text="✨ Готово", callback_data="finish_emo_selection")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
