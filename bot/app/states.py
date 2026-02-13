from aiogram.fsm.state import StatesGroup, State


class CreateTicket(StatesGroup):
    branch = State()
    device_type = State()
    brand_model = State()
    problem = State()
    photos = State()
    urgency = State()
    phone = State()
