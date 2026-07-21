from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from states import FeedbackState
from config import ADMIN_ID

router = Router()

@router.message(Command("feedback", "bug"))
async def cmd_feedback(message: Message, state: FSMContext):
    await message.answer(
        "Опишите проблему или оставьте предложение по улучшению бота.\n"
        "Вы можете отправить текст, фото или скриншот.\n\n"
        "Для отмены отправьте команду /cancel."
    )
    await state.set_state(FeedbackState.waiting_for_feedback)

@router.message(FeedbackState.waiting_for_feedback, Command("cancel"))
async def cmd_cancel_feedback(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отправка обратной связи отменена.")

@router.message(FeedbackState.waiting_for_feedback)
async def process_feedback(message: Message, state: FSMContext):
    user_info = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
    header = f"📩 **Новый отзыв от {user_info}** (`{message.from_user.id}`):\n\n"

    try:
        if message.text:
            await message.bot.send_message(
                chat_id=ADMIN_ID,
                text=header + message.text,
                parse_mode="Markdown"
            )
        else:
            await message.bot.send_message(
                chat_id=ADMIN_ID,
                text=header,
                parse_mode="Markdown"
            )
            await message.forward(chat_id=ADMIN_ID)

        await message.answer("Спасибо за обратную связь! Сообщение отправлено разработчику.")
    except Exception as e:
        await message.answer("Произошла ошибка при отправке. Попробуйте позже.")
        print(f"Ошибка отправки фидбека: {e}")

    await state.clear()
