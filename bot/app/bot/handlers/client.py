# app/bot/handlers/client.py
from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text, Command
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton

from app.models.client import Client
from app.models.ticket import Ticket, DeliveryMethod
from app.database import SessionLocal
from app.bot.states.ticket import TicketState
import app.bot.services.ticket_service as ticket_service

from .common import (
    build_keyboard, branch_kb, urgency_kb,
    build_master_select_keyboard, CATEGORIES, BRANDS,
    client_main_keyboard
)
from app.bot.bot import MASTER_GROUP_ID

def register_client_handlers(dp: Dispatcher):
    
    # ---------- КОМАНДЫ ДЛЯ НАВИГАЦИИ ----------
    @dp.message_handler(Command("start"))
    async def start_command(message: types.Message, state: FSMContext):
        """Команда /start - главное меню"""
        await state.finish()
        
        welcome_text = """
👋 Добро пожаловать в сервисный центр TechRepair!

Мы предоставляем качественный ремонт техники:
📱 Телефоны и планшеты
💻 Ноутбуки и компьютеры
🎮 Игровые консоли
⌚ Умные часы

Выберите действие:
"""
        await message.answer(welcome_text, reply_markup=client_main_keyboard())
    
    @dp.message_handler(Command("menu"))
    async def menu_command(message: types.Message, state: FSMContext):
        """Команда /menu - возврат в главное меню"""
        await state.finish()
        await message.answer("📋 Главное меню:", reply_markup=client_main_keyboard())
    
    @dp.message_handler(Command("cancel"), state="*")
    async def cancel_command(message: types.Message, state: FSMContext):
        """Команда /cancel - отмена текущего действия"""
        current_state = await state.get_state()
        if current_state is None:
            return
        
        await state.finish()
        await message.answer(
            "❌ Действие отменено. Возвращаю вас в главное меню.",
            reply_markup=client_main_keyboard()
        )
    
    # ---------- START TICKET WITH 3 METHODS ----------
    @dp.message_handler(Text(equals="📥 Создать заявку"))
    async def start_ticket(message: types.Message, state: FSMContext):
        await state.finish()
        
        # Клавиатура с 3 способами
        delivery_kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton("🚶 Принесу сам")],
                [KeyboardButton("🚚 Заберу курьером")],
                [KeyboardButton("❌ Отмена")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await message.answer(
            "📦 Как вы хотите передать устройство?\n\n"
            "• 🚶 Принесу сам - быстрее и дешевле\n"
            "• 🚚 Заберу курьером - удобно, но с доплатой",
            reply_markup=delivery_kb
        )
        await TicketState.delivery_method.set()
    
    # ---------- DELIVERY METHOD SELECTION ----------
    @dp.message_handler(state=TicketState.delivery_method)
    async def select_delivery_method(message: types.Message, state: FSMContext):
        if message.text == "❌ Отмена":
            await state.finish()
            await message.answer("❌ Создание заявки отменено", 
                               reply_markup=client_main_keyboard())
            return
        
        if message.text == "🚶 Принесу сам":
            await state.update_data(delivery_method=DeliveryMethod.PICKUP.value)
            await message.answer("📍 Выберите филиал:", reply_markup=branch_kb)
            await TicketState.branch.set()
            
        elif message.text == "🚚 Заберу курьером":
            await state.update_data(delivery_method=DeliveryMethod.DELIVERY.value)
            
            delivery_info = """
🚚 КУРЬЕРСКАЯ ДОСТАВКА:

🏠 Введите адрес для курьера:
Пример: Душанбе, проспект Рудаки, 15, кв. 42
"""
            await message.answer(
                delivery_info,
                reply_markup=ReplyKeyboardRemove()
            )
            await TicketState.delivery_address.set()
    
    # ---------- DELIVERY FLOW (КУРЬЕР) ----------
    @dp.message_handler(state=TicketState.delivery_address)
    async def get_delivery_address(message: types.Message, state: FSMContext):
        if len(message.text.strip()) < 10:
            await message.answer("⚠️ Адрес слишком короткий. Пожалуйста, укажите полный адрес:")
            return
        
        await state.update_data(delivery_address=message.text)
        
        await message.answer("📞 Введите телефон для связи с курьером:\n"
                           "Пример: +992 90 123 45 67")
        await TicketState.delivery_phone.set()
    
    @dp.message_handler(state=TicketState.delivery_phone)
    async def get_delivery_phone(message: types.Message, state: FSMContext):
        phone = message.text.strip()
        if len(phone.replace(" ", "").replace("+", "")) < 9:
            await message.answer("⚠️ Номер телефона слишком короткий. Пожалуйста, введите правильный номер:")
            return
        
        await state.update_data(delivery_phone=phone)
        
        date_kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton("Сегодня (9:00-19:00)"), KeyboardButton("Завтра (9:00-19:00)")],
                [KeyboardButton("Послезавтра"), KeyboardButton("Укажу позже в комментариях")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await message.answer("📅 Когда удобно принять курьера?", reply_markup=date_kb)
        await TicketState.delivery_date.set()
    
    @dp.message_handler(state=TicketState.delivery_date)
    async def get_delivery_date(message: types.Message, state: FSMContext):
        await state.update_data(delivery_date=message.text)
        await message.answer(
            "📝 Дополнительные пожелания для курьера?\n"
            "Например: 'Звонить в домофон 42', 'Не звонить до 14:00'\n"
            "Напишите 'Нет' если нет",
            reply_markup=ReplyKeyboardRemove()
        )
        await TicketState.delivery_notes.set()
    
    @dp.message_handler(state=TicketState.delivery_notes)
    async def get_delivery_notes(message: types.Message, state: FSMContext):
        if message.text.lower() != "нет":
            await state.update_data(delivery_notes=message.text)
        
        branches_info = """
📍 Выберите филиал:

🏢 ДУШАНБЕ:
• Адрес: ул. Мирзо Турсунзода, 45
• Телефон: +992 37 123 45 67
• Часы: 9:00-19:00 (Пн-Сб)

🏢 ХУДЖАНД:
• Адрес: ул. Ленина, 123
• Телефон: +992 92 123 45 67
• Часы: 9:00-18:00 (Пн-Сб)
"""
        await message.answer(branches_info, reply_markup=branch_kb)
        await TicketState.branch.set()
    
    # ---------- COMMON FLOW (после выбора способа) ----------
    @dp.message_handler(state=TicketState.branch)
    async def branch(message: types.Message, state: FSMContext):
        await state.update_data(branch=message.text)
        
        categories_info = """
📂 Выберите категорию устройства:
"""
        await message.answer(categories_info, reply_markup=build_keyboard(CATEGORIES.keys()))
        await TicketState.category.set()
    
    @dp.message_handler(state=TicketState.category)
    async def category(message: types.Message, state: FSMContext):
        if message.text not in CATEGORIES:
            await message.answer("⚠️ Пожалуйста, выберите категорию через кнопки ниже:")
            return
        
        await state.update_data(category=message.text)
        
        # Убираем информацию о ценах, сразу показываем подкатегории
        await message.answer(
            "📁 Выберите тип устройства:",
            reply_markup=build_keyboard(CATEGORIES[message.text])
        )
        await TicketState.subcategory.set()
    
    @dp.message_handler(state=TicketState.subcategory)
    async def subcategory(message: types.Message, state: FSMContext):
        await state.update_data(subcategory=message.text)
        brands = BRANDS.get(message.text, ["Другое"])
        
        brands_info = """
🏷 Выберите бренд устройства:

Если вашего бренда нет в списке, выберите "Другое"
"""
        await message.answer(brands_info, reply_markup=build_keyboard(brands))
        await TicketState.brand.set()
    
    @dp.message_handler(state=TicketState.brand)
    async def brand(message: types.Message, state: FSMContext):
        if message.text == "Другое":
            await message.answer("✍️ Введите бренд вручную:", reply_markup=ReplyKeyboardRemove())
            await TicketState.custom_brand.set()
            return
        
        await state.update_data(brand=message.text)
        await message.answer(
            "🛠 Опишите проблему подробно:\n\n"
            "Примеры хороших описаний:\n"
            "• 'Не включается, мигает индикатор'\n"
            "• 'Разбит экран, не реагирует на касания'\n"
            "• 'Не заряжается, быстро разряжается'\n"
            "• 'Греется, выключается при нагрузке'",
            reply_markup=ReplyKeyboardRemove()
        )
        await TicketState.problem.set()
    
    @dp.message_handler(state=TicketState.custom_brand)
    async def custom_brand(message: types.Message, state: FSMContext):
        if len(message.text.strip()) < 2:
            await message.answer("⚠️ Бренд слишком короткий. Введите название производителя:")
            return
        
        await state.update_data(brand=message.text)
        await message.answer(
            "🛠 Опишите проблему подробно:\n\n"
            "Примеры хороших описаний:\n"
            "• 'Не включается, мигает индикатор'\n"
            "• 'Разбит экран, не реагирует на касания'\n"
            "• 'Не заряжается, быстро разряжается'",
            reply_markup=ReplyKeyboardRemove()
        )
        await TicketState.problem.set()
    
    @dp.message_handler(state=TicketState.problem)
    async def problem(message: types.Message, state: FSMContext):
        if len(message.text.strip()) < 10:
            await message.answer("⚠️ Описание слишком короткое. Пожалуйста, опишите проблему подробнее:")
            return
        
        await state.update_data(problem=message.text)
        
        photos_info = """
📸 ФОТОГРАФИИ УСТРОЙСТВА

Отправьте 1-3 фотографии устройства:
1. Общий вид (перед, зад)
2. Место повреждения (если есть)
3. Серийный номер/IMEI

⚠️ Важно: Фото должны быть четкими!

Когда закончите, напишите ГОТОВО или нажмите кнопку ниже.
"""
        
        ready_kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton("✅ ГОТОВО")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await message.answer(photos_info, reply_markup=ready_kb)
        await TicketState.photos.set()
    
    @dp.message_handler(content_types=types.ContentType.PHOTO, state=TicketState.photos)
    async def photo(message: types.Message, state: FSMContext):
        data = await state.get_data()
        photos = data.get("photos", [])
        photos.append(message.photo[-1].file_id)
        await state.update_data(photos=photos)
        
        count = len(photos)
        if count == 1:
            await message.answer("✅ Фото 1/3 загружено. Можно еще 2 фото или напишите ГОТОВО")
        elif count == 2:
            await message.answer("✅ Фото 2/3 загружено. Можно еще 1 фото или напишите ГОТОВО")
        elif count == 3:
            await message.answer("✅ Фото 3/3 загружено. Максимум достигнут. Напишите ГОТОВО")
    
    # app/bot/handlers/client.py

# ... (весь предыдущий код до функции finish_photos остается без изменений) ...

    @dp.message_handler(Text(equals=["готово", "✅ ГОТОВО"], ignore_case=True), state=TicketState.photos)
    async def finish_photos(message: types.Message, state: FSMContext):
        data = await state.get_data()
        photos_count = len(data.get("photos", []))
        
        if photos_count == 0:
            # Создаем клавиатуру с кнопками ДА/НЕТ
            confirm_kb = ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton("✅ ДА, продолжить"),
                        KeyboardButton("❌ НЕТ, добавить фото")
                    ]
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )
            
            await message.answer(
                "⚠️ Вы не отправили ни одного фото.\n\n"
                "Желаете продолжить без фото?",
                reply_markup=confirm_kb
            )
            await TicketState.confirm_no_photos.set()
            return
        
        await message.answer(
            "⏳ Укажите срочность ремонта:\n\n"
            "• Обычная - 1-3 рабочих дня\n"
            "• Срочно - приоритет, +30% к стоимости",
            reply_markup=urgency_kb
        )
        await TicketState.urgency.set()
    
    @dp.message_handler(state=TicketState.confirm_no_photos)
    async def confirm_no_photos(message: types.Message, state: FSMContext):
        if message.text in ["✅ ДА, продолжить", "да", "yes", "ок", "ok"]:
            await message.answer(
                "⏳ Укажите срочность ремонта:\n\n"
                "• Обычная - 1-3 рабочих дня\n"
                "• Срочно - приоритет, +30% к стоимости",
                reply_markup=urgency_kb
            )
            await TicketState.urgency.set()
        elif message.text in ["❌ НЕТ, добавить фото", "нет", "no"]:
            await message.answer(
                "📸 Пожалуйста, отправьте фото устройства.\n"
                "Можно отправить до 3 фотографий.\n"
                "Когда закончите, нажмите кнопку ✅ ГОТОВО",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton("✅ ГОТОВО")]],
                    resize_keyboard=True,
                    one_time_keyboard=True
                )
            )
            await TicketState.photos.set()
        else:
            # Если пользователь отправил что-то другое, повторяем вопрос
            confirm_kb = ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton("✅ ДА, продолжить"),
                        KeyboardButton("❌ НЕТ, добавить фото")
                    ]
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )
            
            await message.answer(
                "⚠️ Пожалуйста, выберите один из вариантов:\n\n"
                "✅ ДА, продолжить - создать заявку без фото\n"
                "❌ НЕТ, добавить фото - вернуться к загрузке фото",
                reply_markup=confirm_kb
            )

# ... (остальной код без изменений) ...
    
    @dp.message_handler(state=TicketState.urgency)
    async def finish_ticket(message: types.Message, state: FSMContext):
        await state.update_data(client_id=message.from_user.id)
        await state.update_data(telegram_username=message.from_user.username)
        data = await state.get_data()
        telegram_user = message.from_user
        
        ticket_id = ticket_service.create_ticket(data, telegram_user)
        
        delivery_text = ""
        if data.get('delivery_method') == DeliveryMethod.DELIVERY.value:
            delivery_text = f"""
🚚 Доставка курьером:
🏠 Адрес: {data.get('delivery_address')}
📞 Телефон: {data.get('delivery_phone')}
📅 Дата: {data.get('delivery_date')}
📝 Примечания: {data.get('delivery_notes', 'нет')}
"""
        else:
            delivery_text = "🚶 Вы принесете устройство сами"
        
        next_steps = """
📋 ЧТО ДАЛЬШЕ:

1. ⏳ Ожидайте назначения мастера (в течение часа)
2. 👷 Мастер свяжется для уточнения деталей
3. 🔧 Диагностика и расчет стоимости
4. ✅ Согласование и ремонт
5. 📱 Уведомление о готовности

Вы будете получать уведомления об изменении статуса.
"""
        
        success_message = f"""
✅ Заявка #{ticket_id} создана успешно!

{delivery_text}

📝 ИНФОРМАЦИЯ О ЗАЯВКЕ:
📍 Филиал: {data.get('branch')}
📂 Категория: {data.get('category')}
📁 Тип: {data.get('subcategory')}
🏷 Бренд: {data.get('brand')}
🛠 Проблема: {data.get('problem')}
⚡ Срочность: {data.get('urgency')}
📸 Фото: {len(data.get('photos', []))} шт.

{next_steps}

💬 Для проверки статуса используйте кнопку "📋 Мои заявки"
📞 Для вопросов: +992 123 45 67 89
"""
        
        await message.answer(success_message, reply_markup=client_main_keyboard())
        
        await notify_masters_group(message.bot, ticket_id, data)
        
        await state.finish()
    
    # ---------- MY TICKETS ----------
    # ---------- MY TICKETS ----------
    @dp.message_handler(Text(equals="📋 Мои заявки"))
    async def show_my_tickets(message: types.Message):
        db = SessionLocal()
        
        try:
            client = db.query(Client).filter(
                Client.telegram_id == str(message.from_user.id)
            ).first()
            
            if not client:
                no_tickets_message = """
    📭 У вас еще нет заявок
    
    Хотите создать первую заявку?
    Нажмите "📥 Создать заявку" ниже!
    
    Перед созданием заявки:
    1. Подготовьте устройство
    2. Сфотографируйте проблему
    3. Знайте модель устройства
    """
                await message.answer(no_tickets_message, reply_markup=client_main_keyboard())
                return
            
            tickets = db.query(Ticket).filter(
                Ticket.client_id == client.id
            ).order_by(Ticket.created_at.desc()).limit(10).all()
            
            if not tickets:
                await message.answer("У вас еще нет заявок\n\n"
                                   "Создайте первую заявку с помощью кнопки '📥 Создать заявку'")
                return
            
            text = "📋 ВАШИ ЗАЯВКИ:\n\n"
            
            active_count = 0
            completed_count = 0
            
            for ticket in tickets:
                if ticket.status == "✅ Готово":
                    completed_count += 1
                else:
                    active_count += 1
                
                status_emoji = {
                    "Новая": "🆕",
                    "🧪 Диагностика": "🔍",
                    "🔧 В ремонте": "🛠️",
                    "✅ Готово": "✅"
                }.get(ticket.status, "📝")
                
                delivery_info = ""
                if ticket.delivery_method == DeliveryMethod.DELIVERY.value:
                    delivery_info = "🚚"
                elif ticket.delivery_method == DeliveryMethod.PICKUP.value:
                    delivery_info = "🚶"
                
                text += f"{status_emoji}{delivery_info} Заявка #{ticket.id}\n"
                text += f"📱 {ticket.brand} - {ticket.problem[:30]}...\n"
                text += f"📊 Статус: {ticket.status}\n"
                
                if ticket.master:
                    text += f"👷 Мастер: {ticket.master.name}\n"
                
                if ticket.status == "✅ Готово":
                    text += f"✅ Завершено: {ticket.created_at.strftime('%d.%m.%Y')}\n"
                else:
                    text += f"📅 Создано: {ticket.created_at.strftime('%d.%m.%Y')}\n"
                
                text += "─" * 20 + "\n"
            
            stats_text = f"""
    📊 СТАТИСТИКА:
    🔄 Активных: {active_count}
    ✅ Завершенных: {completed_count}
    📦 Всего: {len(tickets)}
    """
            
            await message.answer(text + stats_text, reply_markup=client_main_keyboard())
                
        except Exception as e:
            print(f"Ошибка при получении заявок: {e}")
            await message.answer("❌ Произошла ошибка при получении заявок", 
                               reply_markup=client_main_keyboard())
        finally:
            db.close()
        # ---------- STATUS CHECK ----------
    @dp.message_handler(Text(equals="⏳ Статус ремонта"))
    async def check_repair_status(message: types.Message):
        db = SessionLocal()
        
        try:
            client = db.query(Client).filter(
                Client.telegram_id == str(message.from_user.id)
            ).first()
            
            if not client:
                await message.answer("У вас нет активных заявок", 
                                   reply_markup=client_main_keyboard())
                return
            
            active_tickets = db.query(Ticket).filter(
                Ticket.client_id == client.id,
                Ticket.status != "✅ Готово"
            ).order_by(Ticket.created_at.desc()).all()
            
            if not active_tickets:
                status_message = """
✅ Все заявки завершены

Нет активных заявок в работе.
Все ваши устройства отремонтированы и готовы к выдаче.

📋 Для просмотра истории заявок нажмите "Мои заявки"
📥 Для создания новой заявки нажмите "Создать заявку"
"""
                await message.answer(status_message, reply_markup=client_main_keyboard())
                return
            
            text = "⏳ АКТИВНЫЕ ЗАЯВКИ В РАБОТЕ:\n\n"
            
            for ticket in active_tickets:
                status_details = {
                    "Новая": "🆕 Ожидает назначения мастера",
                    "🧪 Диагностика": "🔍 Проводится диагностика",
                    "🔧 В ремонте": "🛠️ Устройство в ремонте"
                }.get(ticket.status, ticket.status)
                
                text += f"📦 Заявка #{ticket.id}\n"
                text += f"📱 {ticket.brand}\n"
                text += f"📊 {status_details}\n"
                
                if ticket.master:
                    text += f"👷 Мастер: {ticket.master.name}\n"
                
                if ticket.estimated_completion:
                    text += f"⏰ Примерное время: {ticket.estimated_completion}\n"
                else:
                    if ticket.status == "Новая":
                        text += "⏰ Мастер назначится в течение часа\n"
                    elif ticket.status == "🧪 Диагностика":
                        text += "⏰ Диагностика займет 1-2 часа\n"
                    elif ticket.status == "🔧 В ремонте":
                        text += "⏰ Ремонт обычно занимает 1-3 дня\n"
                
                text += "─" * 20 + "\n"
            
            support_info = """
📞 ДЛЯ ВОПРОСОВ:
Телефон: +992 123 45 67 89
Email: support@techrepair.tj

⏱️ Работаем: Пн-Сб 9:00-19:00
"""
            
            await message.answer(text + support_info, reply_markup=client_main_keyboard())
                
        except Exception as e:
            print(f"Ошибка при проверке статуса: {e}")
            await message.answer("❌ Произошла ошибка", reply_markup=client_main_keyboard())
        finally:
            db.close()
    
    # ---------- ABOUT US ----------
    @dp.message_handler(Text(equals="ℹ️ О нас"))
    async def show_about(message: types.Message):
        about_text = """
🤖 Сервисный центр "TechRepair"

🌟 НАШИ ПРЕИМУЩЕСТВА:
• ✅ Гарантия до 12 месяцев
• ⏱️ Быстрая диагностика (30 минут)
• 💰 Прозрачные цены
• 🔧 Оригинальные запчасти
• 👨‍🔧 Опытные мастера

📍 ФИЛИАЛЫ:
🏢 Душанбе
  Адрес: ул. Мирзо Турсунзода, 45
  Часы: Пн-Сб 9:00-19:00
  
🏢 Худжанд
  Адрес: ул. Ленина, 123
  Часы: Пн-Сб 9:00-18:00

🛠️ УСЛУГИ:
• Ремонт телефонов и планшетов
• Ремонт ноутбуков и ПК
• Замена дисплеев и аккумуляторов
• Восстановление данных
• Чистка от вирусов
• Программирование устройств

📞 КОНТАКТЫ:
Телефон: +992 123 45 67 89
Email: info@techrepair.tj
Telegram: @techrepair_support

💎 Работаем с 2015 года
✅ Более 10,000 довольных клиентов
✨ Ваша техника в надежных руках!
"""
        await message.answer(about_text, reply_markup=client_main_keyboard())
    
    # ---------- SUPPORT ----------
    @dp.message_handler(Text(equals="💬 Поддержка"))
    async def show_support(message: types.Message):
        support_text = """
💬 ТЕХНИЧЕСКАЯ ПОДДЕРЖКА

📞 Телефоны:
• Основной: +992 123 45 67 89
• Менеджер: +992 90 123 45 67
• Курьер: +992 93 123 45 67

📧 Email:
• Общие вопросы: info@techrepair.tj
• Поддержка: support@techrepair.tj
• Рекламации: complaints@techrepair.tj

🕐 ВРЕМЯ РАБОТЫ:
Понедельник - Пятница: 9:00 - 19:00
Суббота: 10:00 - 17:00
Воскресенье: выходной

📱 МЕССЕНДЖЕРЫ:
• Telegram: @techrepair_support
• WhatsApp: +992 123 45 67 89
• Instagram: @techrepair_tj

⚡ СРОЧНАЯ ПОМОЩЬ:
Для экстренных случаев звоните на основной телефон.
Мы ответим в любое время!

📝 КАК МЫ РАБОТАЕМ:
1. Вы оставляете заявку
2. Мы связываемся в течение 15 минут
3. Бесплатная диагностика
4. Согласование стоимости
5. Качественный ремонт
6. Гарантия на работу
"""
        await message.answer(support_text, reply_markup=client_main_keyboard())

async def notify_masters_group(bot, ticket_id: int, ticket_data: dict):
    """Уведомление мастеров о новой заявке"""
    delivery_text = ""
    if ticket_data.get('delivery_method') == DeliveryMethod.DELIVERY.value:
        delivery_text = f"""
🚚 ДОСТАВКА КУРЬЕРОМ:
🏠 Адрес: {ticket_data.get('delivery_address')}
📞 Телефон: {ticket_data.get('delivery_phone')}
📅 Дата: {ticket_data.get('delivery_date')}
📝 Примечания: {ticket_data.get('delivery_notes', 'нет')}
"""
    else:
        delivery_text = "🚶 Клиент принесет сам"
    
    client_info = f"""
👤 ИНФОРМАЦИЯ О КЛИЕНТЕ:
ID: {ticket_data.get('client_id')}
Telegram: @{ticket_data.get('telegram_username', 'не указан')}
"""
    
    text = f"""
📢 НОВАЯ ЗАЯВКА #{ticket_id}

{delivery_text}

📍 Филиал: {ticket_data.get('branch')}
📂 Категория: {ticket_data.get('category')}
📁 Тип: {ticket_data.get('subcategory')}
🏷 Бренд: {ticket_data.get('brand')}
🛠 Проблема: {ticket_data.get('problem')}
⚡ Срочность: {ticket_data.get('urgency')}
📸 Фото: {len(ticket_data.get('photos', []))} шт.

{client_info}

👇 Выберите мастера для этой заявки:
"""
    
    await bot.send_message(
        MASTER_GROUP_ID,
        text,
        reply_markup=build_master_select_keyboard(ticket_id)
    )