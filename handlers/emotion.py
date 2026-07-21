from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
import database as db
import keyboards as kb

router = Router()

# Временное хранилище выбранных эмоций пользователем во время мультивыбора
# Структура: { user_id: {"cat": "great", "subs": ["Энергия ⚡", "Радость 😊"]} }
_user_selections = {}

# 1. Шаг 1: Выбор категории (отклик на кнопку из первого шага)
@router.callback_query(F.data.startswith("emo_cat:"))
async def process_primary_emotion(callback: CallbackQuery):
    category = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    # Инициализируем выбор пользователя
    _user_selections[user_id] = {
        "category": category,
        "subs": []
    }
    
    await callback.message.edit_text(
        "Отлично! Теперь выберите детали/оттенки вашего состояния (можно выбрать несколько):",
        reply_markup=kb.sub_emotion_keyboard(selected_items=[])
    )
    await callback.answer()

# 2. Шаг 2: Нажатие на конкретную эмоцию (переключатель галочки)
@router.callback_query(F.data.startswith("toggle_emo:"))
async def toggle_sub_emotion(callback: CallbackQuery):
    item = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    if user_id not in _user_selections:
        await callback.answer("Сессия истекла. Начните заново.", show_alert=True)
        return

    selected_subs = _user_selections[user_id]["subs"]
    
    # Если уже выбрано — убираем, если нет — добавляем
    if item in selected_subs:
        selected_subs.remove(item)
    else:
        selected_subs.append(item)
        
    # Обновляем сообщение с новыми галочками
    await callback.message.edit_reply_markup(
        reply_markup=kb.sub_emotion_keyboard(selected_items=selected_subs)
    )
    await callback.answer()

# 3. Шаг 3: Нажатие кнопки «Готово»
@router.callback_query(F.data == "finish_emo_selection")
async def finish_emotion_selection(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    data = _user_selections.pop(user_id, None)
    if not data:
        await callback.answer("Ошибка или сессия устарела.")
        return

    category = data["category"]
    subs = data["subs"]  # Это список выбранных уточняющих эмоций, например ['Энергия ⚡', 'Радость 😊']
    
    subs_str = ", ".join(subs) if subs else "без уточнений"
    
    # 💾 Сохраняем в базу данных (передаем категорию и список через запятую)
    # Убедитесь, что у вас в db.add_emotion_entry (или аналогичной) принимается этот текст
    await db.add_emotion_entry(user_id=user_id, category=category, details=subs_str)
    
    await callback.message.edit_text(
        f"Зафиксировано! 👌\n\n"
        f"<b>Категория:</b> {category}\n"
        f"<b>Уточнения:</b> {subs_str}"
    )
    await callback.answer("Сохранено!")
