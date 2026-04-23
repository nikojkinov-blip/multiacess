from aiogram.fsm.state import State, StatesGroup

class PaymentStates(StatesGroup):
    waiting_amount = State()
    waiting_confirmation = State()
    entering_card = State()

class SupportStates(StatesGroup):
    waiting_message = State()
    waiting_reply = State()

class AdminStates(StatesGroup):
    waiting_broadcast_text = State()
    waiting_broadcast_target = State()
    waiting_user_search = State()
    waiting_reply_text = State()