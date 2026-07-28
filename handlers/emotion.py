from datetime import date
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
import database as db
import keyboards as kb
from emotions import EMOTIONS
from states import CheckinState
from llm import generate_technique, TECHNIQUE_FALLBACKS

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
        await callback.answer("Сессия устарела, начните заново со следующего вопроса.", show_alert=True)
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
async def on_done(callback: CallbackQuery, state: FSMContext):
    primary_key = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id

    sel = _selections.get(user_id)
    if not sel or sel["primary"] != primary_key:
        await callback.answer("Сессия устарела, начните заново со следующего вопроса.", show_alert=True)
        return

    selected = sel["selected"]
    if not selected:
        await callback.answer("Выберите хотя бы один оттенок.", show_alert=True)
        return

    options = EMOTIONS[primary_key]["secondary"]
    labels = [options[i] for i in sorted(selected)]
    secondary_text = ", ".join(labels)
    _selections.pop(user_id, None)

    await state.update_data(primary_key=primary_key, secondary_text=secondary_text)
    await state.set_state(CheckinState.waiting_for_body)

    primary_label = EMOTIONS[primary_key]["label"]
    await callback.message.edit_text(
        f"Записал: {primary_label} → {secondary_text}.\n\n"
        "Как это ощущается в теле? Опишите своими словами (например: сжало грудь, "
        "дрожат руки, тяжесть в животе)."
    )
    await callback.answer()


@router.message(CheckinState.waiting_for_body)
async def on_body_sensation(message: Message, state: FSMContext):
    data = await state.get_data()
    primary_key = data.get("primary_key")
    secondary_text = data.get("secondary_text")
    await state.clear()

    if not primary_key:
        await message.answer("Что-то пошло не так — попробуйте ответить на следующий вопрос заново.")
        return

    body_text = message.text or ""
    user_id = message.from_user.id
    today = date.today().isoformat()

    await db.save_entry(user_id, primary_key, secondary_text, today, body_text)

    primary_label = EMOTIONS[primary_key]["label"]
    technique = await generate_technique(primary_label, secondary_text, body_text)
    if not technique:
        technique = TECHNIQUE_FALLBACKS.get(
            primary_key, "Дайте себе пару минут просто побыть с этим ощущением, без оценки."
        )

    await message.answer(f"Спасибо, записал.\n\n{technique}")
