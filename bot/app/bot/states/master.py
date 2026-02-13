from aiogram.dispatcher.filters.state import State, StatesGroup


class AddMaster(StatesGroup):

    name = State()
    surname = State()
    phone = State()
    specialization = State()
    experience = State()
    skills = State()
    
class EditMaster(StatesGroup):

    name = State()
    surname = State()
    phone = State()
    specialization = State()
    experience = State()
    skills = State()