from aiogram.fsm.state import State, StatesGroup


class NewPostState(StatesGroup):
    waiting_text = State()
    waiting_photo = State()
    waiting_datetime = State()
    waiting_target = State()
