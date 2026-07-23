from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
import logging
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

    logging.info(f"[start] user={user_id} пытаюсь сохранить wake={wake_hour} sleep={hour}")
    try:
        await db.upsert_user(user_id, wake_hour, hour)
        logging.info(f"[start] user={user_id} успешно сохранён в базу")
    except Exception as e:
        logging.error(f"[start] user={user_id} ОШИБКА при сохранении в базу: {e}")
        await callback.message.answer(
            "Не получилось сохранить настройки — техническая ошибка. Попробуйте /start ещё раз."
        )
        await callback.answer()
        return
    _onboarding_state.pop(user_id, None)

    await callback.message.edit_text(
        f"Готово! Подъём в {wake_hour}:00, отбой в {hour}:00.\n"
        "Каждый час в это окно буду спрашивать о вашем состоянии. "
        "В конце дня — сводка и рекомендации.\n\n"
        "Изменить время можно командой /start в любой момент."
    )
    await callback.answer()
