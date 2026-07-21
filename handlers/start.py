from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command

import keyboards as kb
import database as db

router = Router()

# Временное хранилище выборов пользователя до сохранения в БД
user_settings = {}


# --- 1. Команда /start ---
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Давайте настроим график работы бота.\n\n"
        "Во сколько вы обычно **просыпаетесь**?",
        reply_markup=kb.wake_hour_keyboard(),
        parse_mode="Markdown"
    )


# --- 2. Шаг: Выбор часа подъема ---
@router.callback_query(F.data.startswith("set_wake:"))
async def process_wake_time(callback: CallbackQuery):
    # Мгновенно гасим анимацию на кнопке
    await callback.answer()

    wake_hour = callback.data.split(":")[1]
    user_id = callback.from_user.id

    if user_id not in user_settings:
        user_settings[user_id] = {}
    user_settings[user_id]["wake"] = int(wake_hour)

    await callback.message.edit_text(
        f"Принято: подъем в **{wake_hour}:00**.\n\n"
        "Во сколько вы обычно **ложитесь спать**?",
        reply_markup=kb.sleep_hour_keyboard(),
        parse_mode="Markdown"
    )


# --- 3. Шаг: Выбор часа сна ---
@router.callback_query(F.data.startswith("set_sleep:"))
async def process_sleep_time(callback: CallbackQuery):
    # Мгновенно гасим анимацию на кнопке
    await callback.answer()

    sleep_hour = callback.data.split(":")[1]
    user_id = callback.from_user.id

    if user_id not in user_settings:
        user_settings[user_id] = {}
    user_settings[user_id]["sleep"] = int(sleep_hour)

    await callback.message.edit_text(
        f"Запомнил: отход ко сну в **{sleep_hour}:00**.\n\n"
        "Теперь выберите ваш **часовой пояс**:",
        reply_markup=kb.timezone_keyboard(),
        parse_mode="Markdown"
    )


# --- 4. Шаг: Выбор часового пояса и завершение ---
@router.callback_query(F.data.startswith("set_tz:"))
async def process_timezone(callback: CallbackQuery):
    # Мгновенно гасим анимацию на кнопке
    await callback.answer("Сохраняем...")

    tz = callback.data.split(":")[1]
    user_id = callback.from_user.id

    # Извлекаем сохраненные ранее часы или ставим по умолчанию
    data = user_settings.pop(user_id, {})
    wake_h = data.get("wake", 8)
    sleep_h = data.get("sleep", 23)

    # Безопасное сохранение в базу данных
    try:
        if hasattr(db, 'add_or_update_user'):
            await db.add_or_update_user(user_id=user_id, wake_hour=wake_h, sleep_hour=sleep_h, timezone=tz)
        elif hasattr(db, 'add_user'):
            await db.add_user(user_id, wake_h, sleep_h, tz)
        elif hasattr(db, 'save_user'):
            await db.save_user(user_id, wake_h, sleep_h, tz)
    except Exception as e:
        print(f"Ошибка при вызове базы данных: {e}")

    # Финальное сообщение пользователю
    await callback.message.edit_text(
        "🎉 **Настройка успешно завершена!**\n\n"
        f"⏰ Подъем: **{wake_h}:00**\n"
        f"🌙 Сон: **{sleep_h}:00**\n"
        f"🌍 Часовой пояс: **{tz}**\n\n"
        "Бот готов к работе и будет присылать вам вопросы о самочувствии.",
        parse_mode="Markdown"
    )
