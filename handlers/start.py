from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
import database as db
import keyboards as kb

router = Router()

# Временное хранилище на этапе онбординга (в памяти процесса)
_onboarding_state = {}

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я буду раз в час — с момента подъёма до отбоя — спрашивать, "
        "что вы сейчас чувствуете, а вечером присылать сводку дня и рекомендации.\n\n"
        "Во сколько вы обычно просыпаетесь?",
        reply_markup=kb.wake_hour_keyboard(),
    )

@router.callback_query(F.data.startswith("wake:"))
async def on_wake_selected(callback: CallbackQuery):
    hour = int(callback.data.split(":")[1])
    _onboarding_state[callback.from_user.id] = {"wake_hour": hour}
    await callback.message.edit_text(f"Подъём в {hour}:00. А во сколько отбой?")
    await callback.message.answer("Выберите время отбоя:", reply_markup=kb.sleep_hour_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("sleep:"))
async def on_sleep_selected(callback: CallbackQuery):
    hour = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    state = _onboarding_state.get(user_id, {})
    wake_hour = state.get("wake_hour", 8)

    await db.upsert_user(user_id, wake_hour, hour)
    _onboarding_state.pop(user_id, None)

    await callback.message.edit_text(
        f"Готово! Подъём в {wake_hour}:00, отбой в {hour}:00.\n"
        "Каждый час в это окно буду спрашивать о вашем состоянии. "
        "В конце дня — сводка и рекомендации.\n\n"
        "Изменить время можно командой /start в любой момент."
    )
    await callback.answer()

# Команда для проверки базы данных
@router.message(Command("check_db"))
async def cmd_check_db(message: Message):
    users = await db.get_all_onboarded_users()
    my_id = message.from_user.id
    
    # Ищем текущего пользователя в списке
    user_data = next((u for u in users if u[0] == my_id), None)
    
    if user_data:
        # u[0] - id, u[1] - wake_hour, u[2] - sleep_hour, u[3] - timezone
        _, wake, sleep, tz = user_data
        await message.answer(
            f"✅ Вы есть в базе планировщика!\n\n"
            f"👤 Ваш ID: {my_id}\n"
            f"⏰ Подъём: {wake}:00\n"
            f"🌙 Отбой: {sleep}:00\n"
            f"🌍 Часовой пояс: {tz or 'Europe/Moscow (по умолчанию)'}"
        )
    else:
        await message.answer(
            f"❌ Вас НЕТ в списке пользователей!\n\n"
            f"Бот не отправляет вам часовые опросы. "
            f"Пройдите регистрацию заново через /start и обязательно выберите время отбоя!"
  )
