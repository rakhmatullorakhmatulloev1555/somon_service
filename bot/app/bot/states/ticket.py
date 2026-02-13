# app/bot/states/ticket.py
from aiogram.dispatcher.filters.state import State, StatesGroup

class TicketState(StatesGroup):
    # Общий выбор способа
    delivery_method = State()
    
    # Для самовывоза и доставки
    branch = State()
    category = State()
    subcategory = State()
    brand = State()
    custom_brand = State()  
    problem = State()
    photos = State()
    urgency = State()
    
    confirm_no_photos = State() 
    # Для доставки
    delivery_address = State()
    delivery_phone = State()
    delivery_date = State()
    delivery_notes = State()
    
    # Для клиента без заявки (walk-in)
    walkin_name = State()
    walkin_phone = State()
    walkin_branch = State()
    walkin_category = State()
    walkin_subcategory = State()
    walkin_brand = State()
    walkin_problem = State()
    walkin_urgency = State()