from datetime import date
from aiogram import Router, F
from aiogram.types import CallbackQuery
import database as db
import keyboards as kb
from emotions import EMOTIONS

router = Router()


@router.callback_query(F.data.startswith("p:"))
async def on_primary_selected(callback: CallbackQuery):
    primary_key = callback.data.split(":")[1]
    label = EMOTIONS[primary_key]["label"]

    await callback.message.edit_text(
        f"{label} — а точнее?", reply_markup=kb.secondary_keyboard(primary_key)
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_primary")
async def on_back_to_primary(callback: CallbackQuery):
    await callback.message.edit_text("Что вы сейчас чувствуете?", reply_markup=kb.primary_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("s:"))
async def on_secondary_selected(callback: CallbackQuery):
    _, primary_key, idx_str = callback.data.split(":", 2)
    idx = int(idx_str)
    secondary_label = EMOTIONS[primary_key]["secondary"][idx]

    user_id = callback.from_user.id
    today = date.today().isoformat()

    await db.save_entry(user_id, primary_key, secondary_label, today)

    primary_label = EMOTIONS[primary_key]["label"]
    await callback.message.edit_text(f"Записал: {primary_label} → {secondary_label}. Спасибо!")
    await callback.answer()
