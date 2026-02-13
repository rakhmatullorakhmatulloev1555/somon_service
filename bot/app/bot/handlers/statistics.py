# app/bot/handlers/statistics.py
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging
from datetime import datetime, timedelta

from app.bot.config import ADMIN_IDS
from app.database import SessionLocal
from app.models.ticket import Ticket
from app.models.master import Master
from app.models.client import Client
from app.models.part import Part
from sqlalchemy import func

# Настройка логирования
logger = logging.getLogger(__name__)

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def admin_stats_menu(callback: types.CallbackQuery):
    """Меню статистики для админа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📊 Общая статистика", callback_data="stats_overview"),
        InlineKeyboardButton("📈 Заявки по дням", callback_data="stats_trends"),
        InlineKeyboardButton("💰 Финансы", callback_data="stats_finance"),
        InlineKeyboardButton("👥 Клиенты", callback_data="stats_customers"),
        InlineKeyboardButton("👨‍🔧 Мастера", callback_data="stats_masters"),
        InlineKeyboardButton("📦 Запчасти", callback_data="stats_parts"),
        InlineKeyboardButton("⭐ Рейтинги", callback_data="stats_ratings"),
        InlineKeyboardButton("◀️ Назад", callback_data="admin_menu")
    )
    
    await callback.message.edit_text(
        "📊 <b>СТАТИСТИКА И АНАЛИТИКА</b>\n\n"
        "Выберите раздел для просмотра:\n\n"
        "• Общая статистика - основные показатели\n"
        "• Заявки по дням - динамика обращений\n"
        "• Финансы - выручка и прибыль\n"
        "• Клиенты - активность и новые\n"
        "• Мастера - загрузка и эффективность\n"
        "• Запчасти - остатки и оборот\n"
        "• Рейтинги - оценки мастеров",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

async def stats_overview_callback(callback: types.CallbackQuery):
    """Общая статистика"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    await callback.answer()
    
    db = SessionLocal()
    try:
        # Основные показатели
        total_tickets = db.query(Ticket).count()
        active_tickets = db.query(Ticket).filter(
            Ticket.status.in_(["Новая", "🧪 Диагностика", "🔧 В ремонте", "В работе"])
        ).count()
        completed_tickets = db.query(Ticket).filter(Ticket.status == "✅ Готово").count()
        
        total_masters = db.query(Master).count()
        active_masters = db.query(Master).filter(Master.status == "active").count()
        
        total_clients = db.query(Client).count()
        new_clients_today = db.query(Client).filter(
            func.date(Client.created_at) == datetime.now().date()
        ).count()
        
        # Заявки сегодня
        tickets_today = db.query(Ticket).filter(
            func.date(Ticket.created_at) == datetime.now().date()
        ).count()
        
        # Средний рейтинг
        avg_rating = db.query(func.avg(Master.rating)).filter(
            Master.rating_count > 0
        ).scalar() or 0
        
        # Запчасти с низким запасом
        low_stock_parts = db.query(Part).filter(
            Part.stock < Part.min_stock
        ).count()
        
        text = f"""
📊 <b>ОБЩАЯ СТАТИСТИКА</b>
━━━━━━━━━━━━━━━━━━━━━

📋 <b>ЗАЯВКИ:</b>
• Всего: {total_tickets}
• Активных: {active_tickets}
• Завершено: {completed_tickets}
• Сегодня: {tickets_today}

👥 <b>КЛИЕНТЫ И МАСТЕРА:</b>
• Клиентов: {total_clients}
• Новых сегодня: {new_clients_today}
• Мастеров: {total_masters}
• Активных: {active_masters}

⭐ <b>КАЧЕСТВО:</b>
• Средний рейтинг: {avg_rating:.2f}
• Эффективность: {(completed_tickets/total_tickets*100) if total_tickets > 0 else 0:.1f}%

📦 <b>СКЛАД:</b>
• Низкий запас: {low_stock_parts} позиций
"""
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔄 Обновить", callback_data="stats_overview"))
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="admin_stats_menu"))
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    finally:
        db.close()

async def stats_trends_callback(callback: types.CallbackQuery):
    """Статистика заявок по дням"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    await callback.answer()
    
    db = SessionLocal()
    try:
        text = "📈 <b>ДИНАМИКА ЗАЯВОК (7 дней)</b>\n\n"
        
        for i in range(6, -1, -1):
            date = datetime.now() - timedelta(days=i)
            count = db.query(Ticket).filter(
                func.date(Ticket.created_at) == date.date()
            ).count()
            
            day_name = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"][date.weekday()]
            bar = "█" * min(count, 20)
            text += f"{day_name}: {bar} {count}\n"
        
        # Среднее за неделю
        week_total = db.query(Ticket).filter(
            Ticket.created_at >= datetime.now() - timedelta(days=7)
        ).count()
        week_avg = week_total / 7 if week_total > 0 else 0
        
        text += f"\n📊 Всего за неделю: {week_total} заявок"
        text += f"\n📊 Среднее в день: {week_avg:.1f} заявок"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔄 Обновить", callback_data="stats_trends"))
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="admin_stats_menu"))
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    finally:
        db.close()

async def stats_masters_callback(callback: types.CallbackQuery):
    """Статистика по мастерам"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    await callback.answer()
    
    db = SessionLocal()
    try:
        masters = db.query(Master).filter(
            Master.status == "active"
        ).order_by(Master.rating.desc()).limit(5).all()
        
        text = "👨‍🔧 <b>ТОП МАСТЕРОВ</b>\n\n"
        
        if not masters:
            text += "Нет данных о мастерах"
        else:
            for i, master in enumerate(masters, 1):
                rating_stars = "⭐" * int(master.rating or 0) if (master.rating or 0) > 0 else "Нет оценок"
                text += f"{i}. <b>{master.name} {master.surname or ''}</b>\n"
                text += f"   📊 Рейтинг: {master.rating or 0:.2f} {rating_stars}\n"
                text += f"   ✅ Выполнено: {master.completed_orders or 0}\n"
                text += f"   🔧 В работе: {master.active_orders or 0}\n\n"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("📊 Полный рейтинг", callback_data="stats_ratings"))
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="admin_stats_menu"))
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    finally:
        db.close()

async def stats_ratings_callback(callback: types.CallbackQuery):
    """Рейтинг мастеров"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    await callback.answer()
    
    db = SessionLocal()
    try:
        masters = db.query(Master).filter(
            Master.rating_count > 0
        ).order_by(Master.rating.desc()).all()
        
        if not masters:
            text = "⭐ <b>РЕЙТИНГ МАСТЕРОВ</b>\n\nНет оценок"
        else:
            text = "⭐ <b>РЕЙТИНГ МАСТЕРОВ</b>\n\n"
            
            for i, master in enumerate(masters[:10], 1):
                stars = "⭐" * int(master.rating or 0) + "½" * (int((master.rating or 0) % 1 >= 0.5))
                text += f"{i}. <b>{master.name} {master.surname or ''}</b>\n"
                text += f"   {stars} {master.rating:.2f}\n"
                text += f"   📊 Оценок: {master.rating_count}\n\n"
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="admin_stats_menu"))
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    finally:
        db.close()

async def stats_parts_callback(callback: types.CallbackQuery):
    """Статистика по запчастям"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    await callback.answer()
    
    db = SessionLocal()
    try:
        total_parts = db.query(Part).count()
        total_stock = db.query(func.sum(Part.stock)).scalar() or 0
        total_value = db.query(func.sum(Part.purchase_price * Part.stock)).scalar() or 0
        low_stock = db.query(Part).filter(Part.stock < Part.min_stock).count()
        out_of_stock = db.query(Part).filter(Part.stock == 0).count()
        
        text = f"""
📦 <b>СТАТИСТИКА СКЛАДА</b>

📊 <b>ОБЩАЯ ИНФОРМАЦИЯ:</b>
• Всего наименований: {total_parts}
• Общий остаток: {total_stock} шт.
• Стоимость склада: {total_value:,.0f} сомони

⚠️ <b>ПРОБЛЕМНЫЕ ПОЗИЦИИ:</b>
• Низкий запас: {low_stock}
• Нет в наличии: {out_of_stock}
"""
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔄 Обновить", callback_data="stats_parts"))
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="admin_stats_menu"))
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    finally:
        db.close()

async def stats_customers_callback(callback: types.CallbackQuery):
    """Статистика по клиентам"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    await callback.answer()
    
    db = SessionLocal()
    try:
        total_clients = db.query(Client).count()
        active_clients = db.query(Client).filter(
            Client.tickets.any(Ticket.created_at >= datetime.now() - timedelta(days=30))
        ).count()
        new_clients_week = db.query(Client).filter(
            Client.created_at >= datetime.now() - timedelta(days=7)
        ).count()
        
        text = f"""
👥 <b>СТАТИСТИКА КЛИЕНТОВ</b>

📊 <b>ОБЩАЯ ИНФОРМАЦИЯ:</b>
• Всего клиентов: {total_clients}
• Активных (30 дней): {active_clients}
• Новых за неделю: {new_clients_week}

📈 <b>АКТИВНОСТЬ:</b>
• Среднее заявок на клиента: {db.query(Ticket).count() / total_clients if total_clients > 0 else 0:.1f}
"""
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔄 Обновить", callback_data="stats_customers"))
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="admin_stats_menu"))
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    finally:
        db.close()

async def stats_finance_callback(callback: types.CallbackQuery):
    """Финансовая статистика"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступно только администраторам", show_alert=True)
        return
    
    await callback.answer()
    
    db = SessionLocal()
    try:
        # Заглушка, так как нет данных о ценах
        text = f"""
💰 <b>ФИНАНСОВАЯ СТАТИСТИКА</b>

⚠️ <b>В разработке</b>

Здесь будет отображаться:
• Выручка за период
• Расходы на запчасти
• Прибыль
• Средний чек
• Динамика доходов

📊 Для корректного отображения финансов
   необходимо добавить данные о ценах в заявки.
"""
        
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("◀️ Назад", callback_data="admin_stats_menu"))
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    finally:
        db.close()

def register_statistics_handlers(dp: Dispatcher):
    """Регистрация обработчиков статистики"""
    
    dp.register_callback_query_handler(admin_stats_menu, text="admin_stats_menu")
    dp.register_callback_query_handler(stats_overview_callback, text="stats_overview")
    dp.register_callback_query_handler(stats_trends_callback, text="stats_trends")
    dp.register_callback_query_handler(stats_masters_callback, text="stats_masters")
    dp.register_callback_query_handler(stats_ratings_callback, text="stats_ratings")
    dp.register_callback_query_handler(stats_parts_callback, text="stats_parts")
    dp.register_callback_query_handler(stats_customers_callback, text="stats_customers")
    dp.register_callback_query_handler(stats_finance_callback, text="stats_finance")
    
    logger.info("✅ Обработчики статистики зарегистрированы")