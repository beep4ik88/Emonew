from datetime import date
from aiogram import Router, F
from aiogram.types import CallbackQuery
import database as db
import keyboards as kb
from emotions import EMOTIONS

router = Router()

# Временное хранилище выбранных оттенков на время сессии (в памяти процесса)
# user_id -> {"primary": ключ_эмоции, "selected": {индексы}}
_selections: dict[int, dict] = {}


@router.callback_query(F.data.startswith("p:"))
async def on_primary_selected(callback: CallbackQuery):
    primary_key = callback.data.split(":")[1]
    label = EMOTIONS[primary_key]["label"]
    user_id = callback.from_user.id

    _selections[user_id] = {"primary": primary_key, "selected": set()}

    await callback.message.edit_text(
        f"{label} — выберите один или несколько оттенков, затем нажмите «Готово»:",
        reply_markup=kb.secondary_keyboard(primary_key, selected=set()),
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_primary")
async def on_back_to_primary(callback: CallbackQuery):
    _selections.pop(callback.from_user.id, None)
    await callback.message.edit_text("Что вы сейчас чувствуете?", reply_markup=kb.primary_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("t:"))
async def on_toggle_secondary(callback: CallbackQuery):
    _, primary_key, idx_str = callback.data.split(":", 2)
    idx = int(idx_str)
    user_id = callback.from_user.id

    state = _selections.get(user_id)
    if not state or state["primary"] != primary_key:
        await callback.answer("Сессия устарела, начните заново с /start или следующего вопроса.", show_alert=True)
        return

    if idx in state["selected"]:
        state["selected"].discard(idx)
    else:
        state["selected"].add(idx)

    await callback.message.edit_reply_markup(
        reply_markup=kb.secondary_keyboard(primary_key, selected=state["selected"])
    )
    await callback.answer()


@router.callback_query(F.data.startswith("done:"))
async def on_done(callback: CallbackQuery):
    primary_key = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id

    state = _selections.get(user_id)
    if not state or state["primary"] != primary_key:
        await callback.answer("Сессия устарела, начните заново с /start или следующего вопроса.", show_alert=True)
        return

    selected = state["selected"]
    if not selected:
        await callback.answer("Выберите хотя бы один оттенок.", show_alert=True)
        return

    options = EMOTIONS[primary_key]["secondary"]
    labels = [options[i] for i in sorted(selected)]
    secondary_text = ", ".join(labels)

    today = date.today().isoformat()
    await db.save_entry(user_id, primary_key, secondary_text, today)
    _selections.pop(user_id, None)

    primary_label = EMOTIONS[primary_key]["label"]
    await callback.message.edit_text(f"Записал: {primary_label} → {secondary_text}. Спасибо!")
    await callback.answer()
