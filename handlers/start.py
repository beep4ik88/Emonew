from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
import logging
import database as db
import keyboards as kb

router = Router()

# Временное хранилище на этапе онбординга (в памяти процесса)
_onboarding_state: dict[int, dict] = {}


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я помогу вести дневник эмоций по методу колеса Плутчика: фиксируем эмоцию, "
        "как она ощущается в теле, и получаем технику, которая поможет себе помочь.\n\n"
        "Отмечаться будем от 2 до 5 раз в день: обязательно в момент подъёма и отхода ко сну, "
        "и ещё до 3 раз — во времена, которые вы выберете сами.\n\n"
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
    state = _onboarding_state.setdefault(user_id, {})
    state["sleep_hour"] = hour

    await callback.message.edit_text(f"Отбой в {hour}:00.")
    await callback.message.answer(
        "Сколько дополнительных отметок в течение дня хотите — от 0 до 3 "
        "(помимо подъёма и отбоя)?",
        reply_markup=kb.extra_count_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("extra_count:"))
async def on_extra_count_selected(callback: CallbackQuery):
    n = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    state = _onboarding_state.setdefault(user_id, {})
    state["extra_count"] = n
    state["extra_hours"] = []

    if n == 0:
        await _finalize_onboarding(callback, user_id)
        return

    state["extra_index"] = 1
    await callback.message.edit_text(
        f"Выберите время для отметки 1 из {n}:", reply_markup=kb.extra_hour_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("extra_hour:"))
async def on_extra_hour_selected(callback: CallbackQuery):
    hour = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    state = _onboarding_state.get(user_id)

    if not state or "extra_count" not in state:
        await callback.answer("Сессия устарела, начните заново с /start.", show_alert=True)
        return

    state["extra_hours"].append(hour)
    n = state["extra_count"]
    idx = state["extra_index"]

    if idx < n:
        state["extra_index"] += 1
        await callback.message.edit_text(
            f"Выберите время для отметки {idx + 1} из {n}:", reply_markup=kb.extra_hour_keyboard()
        )
        await callback.answer()
        return

    await _finalize_onboarding(callback, user_id)


async def _finalize_onboarding(callback: CallbackQuery, user_id: int):
    state = _onboarding_state.get(user_id, {})
    wake_hour = state.get("wake_hour", 8)
    sleep_hour = state.get("sleep_hour", 23)
    extra_hours = sorted(state.get("extra_hours", []))
    extra_hours_str = ",".join(str(h) for h in extra_hours)

    logging.info(
        f"[start] user={user_id} пытаюсь сохранить wake={wake_hour} sleep={sleep_hour} "
        f"extra={extra_hours_str}"
    )
    try:
        await db.upsert_user(user_id, wake_hour, sleep_hour, extra_hours_str)
        logging.info(f"[start] user={user_id} успешно сохранён в базу")
    except Exception as e:
        logging.error(f"[start] user={user_id} ОШИБКА при сохранении в базу: {e}")
        await callback.message.answer(
            "Не получилось сохранить настройки — техническая ошибка. Попробуйте /start ещё раз."
        )
        await callback.answer()
        return

    _onboarding_state.pop(user_id, None)

    times_list = ", ".join(f"{h}:00" for h in extra_hours) if extra_hours else "нет дополнительных"
    await callback.message.edit_text(
        f"Готово!\n"
        f"Подъём: {wake_hour}:00\n"
        f"Отбой: {sleep_hour}:00\n"
        f"Дополнительные отметки: {times_list}\n\n"
        "В эти моменты буду спрашивать о вашем состоянии, а в отбой — ещё пришлю сводку дня.\n\n"
        "Изменить настройки можно командой /start в любой момент."
    )
    await callback.answer()
