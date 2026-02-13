# app/bot/handlers/admin.py
import logging
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher import Dispatcher
from app.models.ticket import DeliveryMethod

from app.models.master import Master
from app.models.ticket import Ticket
from app.database import SessionLocal
from app.bot.config import ADMIN_IDS
from app.bot.states.master import AddMaster, EditMaster
import app.bot.services.ticket_service as ticket_service
from app.services.master_service import create_master, get_all_masters
from aiogram.utils.exceptions import NetworkError, RetryAfter
from asyncio import sleep

from .common import admin_main_keyboard

# Настройка логирования
logger = logging.getLogger(__name__)

# ==========================
# UTILS
# ==========================

def is_admin(user_id):
    return user_id in ADMIN_IDS

def admin_menu():
    """Клавиатура для админ-панели"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Все заявки", callback_data="admin_tickets")],
        [InlineKeyboardButton(text="👨‍🔧 Мастера", callback_data="admin_masters")],
        [InlineKeyboardButton(text="➕ Добавить мастера", callback_data="add_master_fsm")],
        [],
        [InlineKeyboardButton(text="🔧 УПРАВЛЕНИЕ ЗАПЧАСТЯМИ", callback_data="parts_menu")],
        [
            InlineKeyboardButton(text="📦 Запчасти", callback_data="parts_list"),
            InlineKeyboardButton(text="➕ Добавить", callback_data="parts_add")
        ],
        [
            InlineKeyboardButton(text="🏷️ Категории", callback_data="parts_categories_menu"),
            InlineKeyboardButton(text="🚚 Поставщики", callback_data="parts_suppliers_menu")
        ],
        [InlineKeyboardButton(text="⚠️ Низкий запас", callback_data="parts_low_stock")],
        [],
        [InlineKeyboardButton(text="📊 СТАТИСТИКА", callback_data="admin_stats_menu")],
        [InlineKeyboardButton(text="📈 Полный отчет", callback_data="admin_stats_detailed")]
    ])

# ==========================
# ADMIN PANEL
# ==========================

def register_admin_handlers(dp: Dispatcher):
    
    @dp.message_handler(commands=["admin"])
    async def admin_panel(message: types.Message):
        if not is_admin(message.from_user.id):
            await message.answer("⛔ Доступно только администраторам")
            return
        await message.answer("⚙️ Админ панель", reply_markup=admin_menu())
    
    # ==========================
    # ВОЗВРАТ В АДМИН МЕНЮ
    # ==========================
    
    @dp.callback_query_handler(Text(equals="admin_menu"))
    async def admin_menu_callback(callback: types.CallbackQuery):
        """Обработчик кнопки 'Назад' в админку"""
        if not is_admin(callback.from_user.id):
            await callback.answer("⛔ Доступно только администраторам", show_alert=True)
            return
        
        await callback.answer()
        await callback.message.edit_text(
            "⚙️ Админ панель",
            reply_markup=admin_menu()
        )
    
    # ==========================
    # FSM ADD MASTER
    # ==========================
    
    @dp.message_handler(commands=["add_master"])
    async def add_master_start(message: types.Message):
        if not is_admin(message.from_user.id):
            return
        await AddMaster.name.set()
        await message.answer("Введите имя мастера:")
    
    @dp.message_handler(state=AddMaster.name)
    async def add_master_name(message: types.Message, state: FSMContext):
        await state.update_data(name=message.text)
        await AddMaster.next()
        await message.answer("Введите фамилию:")
    
    @dp.message_handler(state=AddMaster.surname)
    async def add_master_surname(message: types.Message, state: FSMContext):
        await state.update_data(surname=message.text)
        await AddMaster.next()
        await message.answer("Введите телефон:")
    
    @dp.message_handler(state=AddMaster.phone)
    async def add_master_phone(message: types.Message, state: FSMContext):
        await state.update_data(phone=message.text)
        await AddMaster.next()
        await message.answer("Введите специализацию:")
    
    @dp.message_handler(state=AddMaster.specialization)
    async def add_master_spec(message: types.Message, state: FSMContext):
        await state.update_data(specialization=message.text)
        await AddMaster.next()
        await message.answer("Введите опыт (число лет):")
    
    @dp.message_handler(state=AddMaster.experience)
    async def add_master_exp(message: types.Message, state: FSMContext):
        try:
            exp = int(message.text)
        except:
            await message.answer("Введите число!")
            return
        await state.update_data(experience=exp)
        await AddMaster.next()
        await message.answer("Введите навыки через запятую:")
    
    @dp.message_handler(state=AddMaster.skills)
    async def add_master_finish(message: types.Message, state: FSMContext):
        data = await state.get_data()
        
        # Преобразуем навыки в строку
        skills = [s.strip() for s in message.text.split(",")]
        skills_str = ", ".join(skills)
        
        db = SessionLocal()
        master_data = {
            "name": data["name"],
            "surname": data["surname"],
            "phone": data["phone"],
            "specialization": data["specialization"],
            "experience": data["experience"],
            "skills": skills_str,
            "status": "active"
        }
        
        # Если есть telegram_id, добавляем его
        if "telegram_id" in data:
            master_data["telegram_id"] = data["telegram_id"]
        
        try:
            master = create_master(db, master_data)
            await message.answer(f"✅ Мастер создан ID {master.id}")
        except Exception as e:
            logger.error(f"Ошибка при создании мастера: {e}")
            await message.answer(f"❌ Ошибка при создании мастера: {str(e)}")
        finally:
            db.close()
            await state.finish()
    
    @dp.callback_query_handler(Text(equals="add_master_fsm"))
    async def add_master_fsm_start(callback: types.CallbackQuery):
        if not is_admin(callback.from_user.id):
            await callback.answer("⛔ Доступно только администраторам", show_alert=True)
            return
        
        await AddMaster.name.set()
        await callback.message.answer("Введите имя мастера:")
        await callback.answer()
    
    # ==========================
    # ALL TICKETS - ИСПРАВЛЕНО!
    # ==========================
    
    @dp.callback_query_handler(Text(equals="admin_tickets"))
    async def admin_tickets_callback(callback: types.CallbackQuery):
        """Показать все заявки для админа"""
        if not is_admin(callback.from_user.id):
            await callback.answer("⛔ Доступно только администраторам", show_alert=True)
            return
        
        await callback.answer()
        
        # Используем существующую функцию из ticket_service
        tickets = ticket_service.get_all_tickets_with_details()
        
        if not tickets:
            kb = InlineKeyboardMarkup().add(
                InlineKeyboardButton("◀️ Назад", callback_data="admin_menu")
            )
            await callback.message.edit_text("📋 Нет заявок в системе", reply_markup=kb)
            return
        
        buttons = []
        for t in tickets[:10]:  # Показываем последние 10 заявок
            # Определяем эмодзи для статуса
            status_emoji = {
                "Новая": "🆕",
                "🧪 Диагностика": "🔍",
                "🔧 В ремонте": "🛠️",
                "✅ Готово": "✅",
                "В работе": "⚙️"
            }.get(t['status'], "📝")
            
            text = f"{status_emoji} #{t['id']} | {t['brand'] or '?'} | {t['status']} | {t['master_name']}"
            
            # Обрезаем слишком длинный текст
            if len(text) > 60:
                text = text[:57] + "..."
            
            buttons.append([
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"admin_ticket_{t['id']}"
                )
            ])
        
        # Добавляем кнопки управления
        buttons.append([
            InlineKeyboardButton("🔄 Обновить", callback_data="admin_tickets"),
            InlineKeyboardButton("◀️ Назад", callback_data="admin_menu")
        ])
        
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        # Статистика
        total = len(tickets)
        new = sum(1 for t in tickets if t['status'] == 'Новая')
        in_progress = sum(1 for t in tickets if t['status'] not in ['✅ Готово', 'Новая'])
        completed = sum(1 for t in tickets if t['status'] == '✅ Готово')
        
        stats_text = f"📊 Всего: {total} | 🆕 Новых: {new} | 🔧 В работе: {in_progress} | ✅ Завершено: {completed}"
        
        await callback.message.edit_text(
            f"📋 <b>ВСЕ ЗАЯВКИ</b>\n\n{stats_text}\n\nВыберите заявку для просмотра:",
            reply_markup=kb,
            parse_mode="HTML"
        )
    
    # app/bot/handlers/admin.py
    @dp.callback_query_handler(lambda c: c.data and c.data.startswith("admin_ticket_"))
    async def admin_ticket_detail_callback(callback: types.CallbackQuery):
        """Просмотр деталей конкретной заявки"""
        if not is_admin(callback.from_user.id):
            await callback.answer("⛔ Доступно только администраторам", show_alert=True)
            return

        await callback.answer()

        # Получаем ID заявки из callback_data
        ticket_id = int(callback.data.split("_")[2])

        # Получаем детали заявки
        ticket = ticket_service.get_ticket(ticket_id)

        if not ticket:
            await callback.message.edit_text(
                "❌ Заявка не найдена",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("◀️ Назад к заявкам", callback_data="admin_tickets")
                )
            )
            return

        # Формируем детальную информацию о заявке
        client_info = ""
        if ticket.client:
            client_info = f"👤 Клиент: {ticket.client.name or 'Без имени'}\n📞 Телефон: {ticket.client.phone or 'Не указан'}"
            if ticket.client.telegram_id:
                client_info += f"\n📱 TG: @{ticket.client.username or 'не указан'}"
        elif ticket.walkin_name:
            client_info = f"👤 Клиент: {ticket.walkin_name}\n📞 Телефон: {ticket.walkin_phone or 'Не указан'}"
        else:
            client_info = "👤 Клиент: не указан"

        master_info = f"👨‍🔧 Мастер: {ticket.master.name if ticket.master else 'Не назначен'}"

        delivery_info = ""
        if ticket.delivery_method == DeliveryMethod.DELIVERY.value:
            delivery_info = f"🚚 Доставка: {ticket.delivery_address}\n📞 Телефон: {ticket.delivery_phone}\n📅 Дата: {ticket.delivery_date or 'Не указана'}"
        elif ticket.delivery_method == DeliveryMethod.PICKUP.value:
            delivery_info = "🚶 Самовывоз"
        else:
            delivery_info = "🏪 В сервисе"

        # Определяем эмодзи для статуса
        status_emoji = {
            "Новая": "🆕",
            "🧪 Диагностика": "🔍",
            "🔧 В ремонте": "🛠️",
            "✅ Готово": "✅",
            "В работе": "⚙️"
        }.get(ticket.status, "📝")

        text = f"""
    📋 <b>ЗАЯВКА #{ticket.id}</b> {status_emoji}

    ━━━━━━━━━━━━━━━━━━━━━
    <b>📌 ИНФОРМАЦИЯ О ЗАЯВКЕ:</b>
    📍 Филиал: {ticket.branch or 'Не указан'}
    📂 Категория: {ticket.category or 'Не указана'}
    📁 Тип: {ticket.subcategory or 'Не указан'}
    🏷 Бренд: {ticket.brand or 'Не указан'}
    🛠 Проблема: {ticket.problem or 'Не указана'}
    ⚡ Срочность: {ticket.urgency or 'Обычная'}
    📊 Статус: {ticket.status}

    ━━━━━━━━━━━━━━━━━━━━━
    <b>👥 КЛИЕНТ И МАСТЕР:</b>
    {client_info}
    {master_info}

    ━━━━━━━━━━━━━━━━━━━━━
    <b>🚚 ДОСТАВКА:</b>
    {delivery_info}

    ━━━━━━━━━━━━━━━━━━━━━
    📅 Создано: {ticket.created_at.strftime('%d.%m.%Y %H:%M') if ticket.created_at else 'Неизвестно'}
    """

        # Кнопки управления
        keyboard = InlineKeyboardMarkup(row_width=2)

        # Кнопки для изменения статуса
        if ticket.status != "✅ Готово":
            if ticket.status == "Новая":
                keyboard.add(
                    InlineKeyboardButton("🔍 В диагностику", callback_data=f"status_diag_{ticket.id}"),
                    InlineKeyboardButton("🔧 В ремонт", callback_data=f"status_repair_{ticket.id}")
                )
            elif ticket.status == "🧪 Диагностика":
                keyboard.add(
                    InlineKeyboardButton("🔧 В ремонт", callback_data=f"status_repair_{ticket.id}"),
                    InlineKeyboardButton("✅ Готово", callback_data=f"status_done_{ticket.id}")
                )
            elif ticket.status == "🔧 В ремонте":
                keyboard.add(
                    InlineKeyboardButton("✅ Готово", callback_data=f"status_done_{ticket.id}")
                )

        # Кнопка назначения мастера
        if not ticket.master:
            keyboard.add(
                InlineKeyboardButton("👨‍🔧 Назначить мастера", callback_data=f"assign_ticket_{ticket.id}")
            )

        # Кнопки навигации
        keyboard.add(
            InlineKeyboardButton("🔄 Обновить", callback_data=f"admin_ticket_{ticket.id}"),
            InlineKeyboardButton("◀️ Назад к заявкам", callback_data="admin_tickets")
        )

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        # ==========================
        # MASTERS LIST
        # ==========================
    
    @dp.callback_query_handler(Text(equals="admin_masters"))
    async def admin_masters_callback(callback: types.CallbackQuery):
        if not is_admin(callback.from_user.id):
            await callback.answer("⛔ Доступно только администраторам", show_alert=True)
            return
        
        await callback.answer()
        
        db = SessionLocal()
        masters = get_all_masters(db)
        db.close()
        
        buttons = []
        for m in masters:
            buttons.append([
                InlineKeyboardButton(
                    text=f"{m.name} {m.surname}",
                    callback_data=f"master_{m.id}"
                )
            ])
        
        # Добавляем кнопку для добавления нового мастера
        buttons.append([
            InlineKeyboardButton(
                text="➕ Добавить мастера",
                callback_data="add_master_fsm"
            )
        ])
        
        buttons.append([
            InlineKeyboardButton("◀️ Назад", callback_data="admin_menu")
        ])
        
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.edit_text("👨‍🔧 Список мастеров:", reply_markup=kb)
    
    # ==========================
    # EDIT MASTER
    # ==========================
    
    @dp.message_handler(commands=["edit_master"])
    async def edit_master_start(message: types.Message):
        if not is_admin(message.from_user.id):
            return
        
        db = SessionLocal()
        masters = get_all_masters(db)
        db.close()
        
        buttons = []
        for m in masters:
            buttons.append([
                InlineKeyboardButton(
                    text=f"{m.name} {m.surname}",
                    callback_data=f"edit_master_{m.id}"
                )
            ])
        
        await message.answer(
            "Выберите мастера для редактирования:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
    
    @dp.callback_query_handler(lambda c: c.data.startswith("edit_master_"))
    async def edit_master_select(callback: types.CallbackQuery, state: FSMContext):
        if not is_admin(callback.from_user.id):
            await callback.answer("⛔ Доступно только администраторам", show_alert=True)
            return
        
        master_id = int(callback.data.split("_")[2])
        await state.update_data(master_id=master_id)
        await EditMaster.name.set()
        await callback.message.answer("Введите новое имя:")
        await callback.answer()
    
    @dp.message_handler(state=EditMaster.name)
    async def edit_master_name(message: types.Message, state: FSMContext):
        await state.update_data(name=message.text)
        await EditMaster.next()
        await message.answer("Введите новую фамилию:")
    
    @dp.message_handler(state=EditMaster.surname)
    async def edit_master_finish(message: types.Message, state: FSMContext):
        data = await state.get_data()
        
        db = SessionLocal()
        master = db.query(Master).get(data["master_id"])
        
        if master:
            master.name = data["name"]
            master.surname = message.text
            db.commit()
            await message.answer("✅ Мастер обновлен")
        else:
            await message.answer("❌ Мастер не найден")
        
        db.close()
        await state.finish()
    
    # ==========================
    # STATISTICS
    # ==========================
    
    @dp.callback_query_handler(Text(equals="admin_stats"))
    async def admin_stats(callback: types.CallbackQuery):
        if not is_admin(callback.from_user.id):
            await callback.answer("⛔ Доступно только администраторам", show_alert=True)
            return
        
        await callback.answer()
        
        db = SessionLocal()
        
        try:
            # Статистика по мастерам
            total_masters = db.query(Master).count()
            active_masters = db.query(Master).filter(Master.status == 'active').count()
            
            # Статистика по заявкам
            total_tickets = db.query(Ticket).count()
            completed_tickets = db.query(Ticket).filter(Ticket.status == '✅ Готово').count()
            new_tickets = db.query(Ticket).filter(Ticket.status == 'Новая').count()
            
            text = f"""
📊 СТАТИСТИКА СИСТЕМЫ:

👥 МАСТЕРЫ:
  • Всего: {total_masters}
  • Активных: {active_masters}

📋 ЗАЯВКИ:
  • Всего: {total_tickets}
  • Новых: {new_tickets}
  • Выполнено: {completed_tickets} ({completed_tickets/total_tickets*100 if total_tickets > 0 else 0:.1f}%)

⚡ АКТИВНОСТЬ:
  • Используйте /admin для управления
  • /add_master для добавления мастера
  • /edit_master для редактирования
"""
            
            await callback.message.edit_text(text)
            
        except Exception as e:
            print(f"Ошибка при получении статистики: {e}")
            await callback.message.edit_text("❌ Ошибка при получении статистики")
        finally:
            db.close()
    
    # ---------- MASTER RATINGS (FOR ADMINS) ----------
    @dp.message_handler(Text(equals="📊 Рейтинги мастеров"))
    async def show_master_ratings_admin(message: types.Message):
        """Показать рейтинги всех мастеров (для админов)"""
        if message.from_user.id not in ADMIN_IDS:
            await message.answer("⛔ Доступно только администраторам")
            return
        
        db = SessionLocal()
        
        try:
            masters = db.query(Master).order_by(Master.rating.desc()).all()
            
            if not masters:
                await message.answer("Нет мастеров в базе данных")
                return
            
            text = "📊 РЕЙТИНГИ МАСТЕРОВ:\n\n"
            
            for i, master in enumerate(masters, 1):
                rating_stars = "⭐" * int(master.rating) if master.rating > 0 else "暂无评分"
                
                text += f"{i}. {master.name} {master.surname or ''}\n"
                text += f"   🏷 {master.specialization}\n"
                text += f"   ⭐ Рейтинг: {master.rating:.2f} ({rating_stars})\n"
                text += f"   📊 Оценок: {master.rating_count}\n"
                
                if master.telegram_id:
                    text += f"   👤 TG ID: {master.telegram_id}\n"
                
                text += "\n"
            
            # Если текст слишком длинный, разбиваем на части
            if len(text) > 4000:
                parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
                for part in parts:
                    await message.answer(part)
            else:
                await message.answer(text)
                
        except Exception as e:
            print(f"Ошибка при получении рейтингов: {e}")
            await message.answer("❌ Произошла ошибка")
        finally:
            db.close()
    
    # ---------- ALL TICKETS (FOR ADMINS) ----------
    @dp.message_handler(Text(equals="📋 Все заявки"))
    async def show_all_tickets(message: types.Message):
        """Показать все заявки (для админов)"""
        if message.from_user.id not in ADMIN_IDS:
            await message.answer("⛔ Доступно только администраторам")
            return
        
        db = SessionLocal()
        
        try:
            from sqlalchemy.orm import joinedload
            
            tickets = db.query(Ticket).options(
                joinedload(Ticket.client),
                joinedload(Ticket.master)
            ).order_by(Ticket.created_at.desc()).limit(20).all()
            
            if not tickets:
                await message.answer("Нет заявок в базе данных")
                return
            
            text = "📋 ПОСЛЕДНИЕ ЗАЯВКИ:\n\n"
            
            for ticket in tickets:
                text += f"#{ticket.id} - {ticket.status}\n"
                text += f"📱 {ticket.brand} - {ticket.problem[:30]}...\n"
                
                if ticket.client:
                    text += f"👤 Клиент: {ticket.client.name or 'Без имени'}\n"
                
                if ticket.master:
                    text += f"👷 Мастер: {ticket.master.name}\n"
                
                text += f"⏰ {ticket.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                text += "─" * 20 + "\n"
            
            await message.answer(text)
                
        except Exception as e:
            print(f"Ошибка при получении заявок: {e}")
            await message.answer("❌ Произошла ошибка")
        finally:
            db.close()
    
    # ---------- MASTERS LIST (FOR ADMINS) ----------
    @dp.message_handler(Text(equals="👥 Мастера"))
    async def show_all_masters(message: types.Message):
        """Показать всех мастеров (для админов)"""
        if message.from_user.id not in ADMIN_IDS:
            await message.answer("⛔ Доступно только администраторам")
            return
        
        db = SessionLocal()
        
        try:
            masters = db.query(Master).all()
            
            if not masters:
                await message.answer("Нет мастеров в базе данных")
                return
            
            text = "👥 ВСЕ МАСТЕРЫ:\n\n"
            
            for i, master in enumerate(masters, 1):
                status_emoji = "🟢" if master.status == 'active' else "🔴"
                
                text += f"{i}. {master.name} {master.surname or ''}\n"
                text += f"   {status_emoji} Статус: {master.status}\n"
                text += f"   🏷 {master.specialization}\n"
                text += f"   ⭐ Рейтинг: {master.rating:.2f} ({master.rating_count} оценок)\n"
                
                if master.telegram_id:
                    text += f"   👤 TG: {master.telegram_id}\n"
                
                if master.phone:
                    text += f"   📞 {master.phone}\n"
                
                if master.skills:
                    text += f"   🔧 Навыки: {master.skills}\n"
                
                text += f"   📊 Заказов: {master.completed_orders} выполнено, {master.active_orders} активно\n"
                text += "\n"
            
            # Добавляем инструкцию
            text += "\n⚡ Команды для управления:\n"
            text += "  • /add_master - добавить мастера\n"
            text += "  • /edit_master - редактировать мастера\n"
            text += "  • /admin - админ панель\n"
            
            # Если текст слишком длинный, разбиваем на части
            if len(text) > 4000:
                parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
                for part in parts:
                    await message.answer(part)
            else:
                await message.answer(text)
                
        except Exception as e:
            print(f"Ошибка при получении мастеров: {e}")
            await message.answer("❌ Произошла ошибка")
        finally:
            db.close()