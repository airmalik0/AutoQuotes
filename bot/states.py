from aiogram.fsm.state import State, StatesGroup


class RegistrationState(StatesGroup):
    waiting_language = State()
    waiting_contact = State()
    waiting_role = State()
    waiting_brands = State()


class SellerResponseState(StatesGroup):
    waiting_price = State()
    waiting_currency = State()
    waiting_availability = State()
    waiting_comment = State()
