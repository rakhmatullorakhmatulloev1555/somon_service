# app/bot/handlers/calendar.py
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.services import event_service
from app.models.master import Master
from app.bot.config import ADMIN_IDS

logger = logging.getLogger(__name__)

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def cmd_calendar(message: types.Message):
    """Календарь событий"""
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("📅 Сегодня", callback_data="cal_today"),
        InlineKeyboardButton("📆 Неделя", callback_data="cal_week"),
        InlineKeyboardButton("🗓️ Месяц", callback_data="cal_month")
    )
    keyboard.add(
        InlineKeyboardButton("➕ Создать событие", callback_data="cal_create"),
        InlineKeyboardButton("📋 Мои события", callback_data="cal_my")
    )
    
    await message.answer(
        "📅 <b>КАЛЕНДАРЬ СОБЫТИЙ</b>\n\n"
        "Выберите период или действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

async def cal_today_callback(callback: types.CallbackQuery):
    """События на сегодня"""
    await callback.answer()
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    events = event_service.get_events(today, tomorrow)
    
    if not events:
        await callback.message.edit_text(
            "📅 <b>СОБЫТИЯ НА СЕГОДНЯ</b>\n\n"
            "На сегодня нет запланированных событий.",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("◀️ Назад", callback_data="calendar")
            ),
            parse_mode="HTML"
        )
        return
    
    text = f"📅 <b>СОБЫТИЯ НА СЕГОДНЯ ({today.strftime('%d.%m.%Y')})</b>\n\n"
    
    for event in events[:10]:
        emoji = {
            "repair": "🔧",
            "delivery": "🚚",
            "meeting": "👥",
            "appointment": "📝",
            "other": "📌"
        }.get(event.event_type, "📌")
        
        time_str = event.start_date.strftime("%H:%M")
        text += f"{emoji} <b>{time_str}</b> - {event.title}\n"
        if event.master:
            text += f"   👨‍🔧 {event.master.name}\n"
        if event.client:
            text += f"   👤 {event.client.name}\n"
        text += "─" * 20 + "\n"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔄 Обновить", callback_data="cal_today"))
    keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="calendar"))
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

async def cal_week_callback(callback: types.CallbackQuery):
    """События на неделю"""
    await callback.answer()
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    week_later = today + timedelta(days=7)
    
    events = event_service.get_events(today, week_later)
    
    text = f"📆 <b>СОБЫТИЯ НА НЕДЕЛЮ ({today.strftime('%d.%m')} - {week_later.strftime('%d.%m')})</b>\n\n"
    
    if not events:
        text += "На эту неделю нет запланированных событий."
    else:
        # Группируем по дням
        days = {}
        for event in events:
            day_key = event.start_date.strftime("%d.%m.%Y")
            if day_key not in days:
                days[day_key] = []
            days[day_key].append(event)
        
        for day_key, day_events in days.items():
            day_name = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"][day_events[0].start_date.weekday()]
            text += f"\n<b>{day_name} {day_key}</b>\n"
            
            for event in day_events[:3]:
                emoji = {
                    "repair": "🔧",
                    "delivery": "🚚",
                    "meeting": "👥",
                    "appointment": "📝",
                    "other": "📌"
                }.get(event.event_type, "📌")
                
                text += f"  {emoji} {event.start_date.strftime('%H:%M')} - {event.title}\n"
            
            if len(day_events) > 3:
                text += f"  ... и еще {len(day_events)-3} событий\n"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("◀️ Назад", callback_data="calendar")
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

async def cal_my_callback(callback: types.CallbackQuery):
    """События мастера"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    await callback.answer()
    
    db = SessionLocal()
    try:
        master = db.query(Master).filter(
            Master.telegram_id == str(callback.from_user.id)
        ).first()
        
        if not master:
            await callback.message.edit_text(
                "❌ Вы не зарегистрированы как мастер",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("◀️ Назад", callback_data="calendar")
                )
            )
            return
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_later = today + timedelta(days=7)
        
        events = event_service.get_master_events(master.id, today, week_later)
        
        if not events:
            await callback.message.edit_text(
                f"📋 <b>ВАШИ СОБЫТИЯ</b>\n\n"
                f"У вас нет запланированных событий на ближайшую неделю.",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("◀️ Назад", callback_data="calendar")
                ),
                parse_mode="HTML"
            )
            return
        
        text = f"📋 <b>ВАШИ СОБЫТИЯ (ближайшая неделя)</b>\n\n"
        
        for event in events:
            date_str = event.start_date.strftime("%d.%m.%Y")
            time_str = event.start_date.strftime("%H:%M")
            emoji = {
                "repair": "🔧",
                "delivery": "🚚",
                "meeting": "👥",
                "appointment": "📝",
                "other": "📌"
            }.get(event.event_type, "📌")
            
            text += f"{emoji} <b>{date_str} {time_str}</b>\n"
            text += f"   {event.title}\n"
            
            if event.ticket_id:
                text += f"   Заявка #{event.ticket_id}\n"
            
            text += "\n"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="calendar"))
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    finally:
        db.close()

def register_calendar_handlers(dp: Dispatcher):
    """Регистрация обработчиков календаря"""
    
    dp.register_message_handler(cmd_calendar, Command("calendar"))
    dp.register_message_handler(cmd_calendar, Text(equals="📅 Календарь"))
    
    dp.register_callback_query_handler(cal_today_callback, text="cal_today")
    dp.register_callback_query_handler(cal_week_callback, text="cal_week")
    dp.register_callback_query_handler(cal_my_callback, text="cal_my")
    dp.register_callback_query_handler(cmd_calendar, text="calendar")
    
    logger.info("✅ Обработчики календаря зарегистрированы")