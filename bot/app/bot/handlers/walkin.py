# app/bot/handlers/walkin.py
from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from app.bot.states.ticket import TicketState
from app.bot.services.ticket_service import create_walkin_ticket
from app.bot.bot import MASTER_GROUP_ID
from app.bot.handlers.common import build_master_select_keyboard, build_keyboard, CATEGORIES, BRANDS, branch_kb, urgency_kb

def register_walkin_handlers(dp: Dispatcher):
    """Обработчики для создания заявок в сервисе"""
    
    # ---------- START WALK-IN TICKET (для администраторов) ----------
    @dp.message_handler(commands=["walkin"])
    async def start_walkin_ticket(message: types.Message, state: FSMContext):
        """Начало создания заявки для клиента в сервисе"""
        # Проверяем права (можно добавить проверку на админа)
        await state.finish()
        await state.update_data(delivery_method="walkin")
        
        await message.answer(
            "👤 Введите имя клиента (кто принес устройство):",
            reply_markup=ReplyKeyboardRemove()
        )
        await TicketState.walkin_name.set()
    
    @dp.message_handler(state=TicketState.walkin_name)
    async def get_walkin_name(message: types.Message, state: FSMContext):
        await state.update_data(walkin_name=message.text)
        await message.answer("📞 Введите телефон клиента:")
        await TicketState.walkin_phone.set()
    
    @dp.message_handler(state=TicketState.walkin_phone)
    async def get_walkin_phone(message: types.Message, state: FSMContext):
        await state.update_data(walkin_phone=message.text)
        await message.answer("📍 Выберите филиал:", reply_markup=branch_kb)
        await TicketState.walkin_branch.set()
    
    @dp.message_handler(state=TicketState.walkin_branch)
    async def get_walkin_branch(message: types.Message, state: FSMContext):
        await state.update_data(branch=message.text)
        await message.answer("📂 Выберите категорию:", 
                           reply_markup=build_keyboard(CATEGORIES.keys()))
        await TicketState.walkin_category.set()
    
    @dp.message_handler(state=TicketState.walkin_category)
    async def get_walkin_category(message: types.Message, state: FSMContext):
        if message.text not in CATEGORIES:
            return await message.answer("Выберите через кнопки")
        
        await state.update_data(category=message.text)
        await message.answer(
            "📁 Выберите подкатегорию:",
            reply_markup=build_keyboard(CATEGORIES[message.text])
        )
        await TicketState.walkin_subcategory.set()
    
    @dp.message_handler(state=TicketState.walkin_subcategory)
    async def get_walkin_subcategory(message: types.Message, state: FSMContext):
        await state.update_data(subcategory=message.text)
        brands = BRANDS.get(message.text, ["Другое"])
        await message.answer("🏷 Выберите бренд:", reply_markup=build_keyboard(brands))
        await TicketState.walkin_brand.set()
    
    @dp.message_handler(state=TicketState.walkin_brand)
    async def get_walkin_brand(message: types.Message, state: FSMContext):
        if message.text == "Другое":
            await message.answer("Введите бренд вручную:")
            return
        
        await state.update_data(brand=message.text)
        await message.answer("🛠 Опишите проблему:")
        await TicketState.walkin_problem.set()
    
    @dp.message_handler(state=TicketState.walkin_problem)
    async def get_walkin_problem(message: types.Message, state: FSMContext):
        await state.update_data(problem=message.text)
        await message.answer("⏳ Укажите срочность:", reply_markup=urgency_kb)
        await TicketState.walkin_urgency.set()
    
    @dp.message_handler(state=TicketState.walkin_urgency)
    async def finish_walkin_ticket(message: types.Message, state: FSMContext):
        data = await state.get_data()
        
        # Создаем walk-in заявку
        ticket_id = create_walkin_ticket(
            client_name=data.get('walkin_name'),
            client_phone=data.get('walkin_phone'),
            branch=data.get('branch'),
            category=data.get('category'),
            brand=data.get('brand'),
            problem=data.get('problem')
        )
        
        await message.answer(f"""
✅ Заявка #{ticket_id} создана для клиента в сервисе!

👤 Клиент: {data.get('walkin_name')}
📞 Телефон: {data.get('walkin_phone')}
📍 Филиал: {data.get('branch')}
📂 Категория: {data.get('category')}
🏷 Бренд: {data.get('brand')}
🛠 Проблема: {data.get('problem')}
⚡ Срочность: {data.get('urgency')}

✅ Мастера уведомлены.
""")
        
        # Уведомляем мастеров
        text = f"""
📢 Новая заявка из сервиса #{ticket_id}

🏪 КЛИЕНТ В СЕРВИСЕ:
👤 Имя: {data.get('walkin_name')}
📞 Телефон: {data.get('walkin_phone')}

📍 Филиал: {data.get('branch')}
📂 Категория: {data.get('category')}
🏷 Бренд: {data.get('brand')}
🛠 Проблема: {data.get('problem')}
⚡ Срочность: {data.get('urgency')}

Выберите мастера:
"""
        
        await message.bot.send_message(
            MASTER_GROUP_ID,
            text,
            reply_markup=build_master_select_keyboard(ticket_id)
        )
        
        await state.finish()