from aiogram.fsm.state import State, StatesGroup


class FeedbackState(StatesGroup):
    waiting_for_feedback = State()


class CheckinState(StatesGroup):
    waiting_for_body = State()
