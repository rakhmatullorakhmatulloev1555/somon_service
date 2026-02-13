# app/api/statistics_api.py
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from sqlalchemy import func, and_, extract
from app.database import SessionLocal
from app.models.ticket import Ticket, DeliveryMethod
from app.models.master import Master
from app.models.client import Client
from app.models.part import Part, PartTransaction
from typing import Optional

router = APIRouter(prefix="/api/statistics")

@router.get("/overview")
async def get_statistics_overview(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Получить общую статистику"""
    db = SessionLocal()
    try:
        # Парсим даты
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.now() - timedelta(days=30)
        
        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = datetime.now()
        
        # Основные показатели
        total_orders = db.query(Ticket).filter(
            Ticket.created_at.between(start, end)
        ).count()
        
        # У Ticket нет поля total_price, используем количество * среднюю цену или 0
        total_revenue = 0  # Заглушка, пока нет данных о ценах
        
        new_customers = db.query(Client).filter(
            Client.created_at.between(start, end)
        ).count()
        
        avg_rating = db.query(func.avg(Master.rating)).filter(
            Master.rating_count > 0
        ).scalar() or 0
        
        completed_orders = db.query(Ticket).filter(
            Ticket.created_at.between(start, end),
            Ticket.status == "✅ Готово"
        ).count()
        
        # Заявки в работе
        in_progress = db.query(Ticket).filter(
            Ticket.created_at.between(start, end),
            Ticket.status.in_(["В работе", "🧪 Диагностика", "🔧 В ремонте"])
        ).count()
        
        total_orders_prev = db.query(Ticket).filter(
            Ticket.created_at.between(
                start - (end - start),
                end - (end - start)
            )
        ).count()
        
        # Расчет эффективности
        efficiency = (completed_orders / total_orders * 100) if total_orders > 0 else 0
        
        # Расчет маржи (заглушка)
        profit_margin = 32.0
        
        # Рост показателей
        orders_growth = ((total_orders - total_orders_prev) / total_orders_prev * 100) if total_orders_prev > 0 else 0
        revenue_growth = 12.0  # Заглушка
        customers_growth = 8.0  # Заглушка
        rating_growth = ((avg_rating - 4.5) / 4.5 * 100) if avg_rating > 0 else 0
        
        return {
            "success": True,
            "data": {
                "kpis": {
                    "totalOrders": total_orders,
                    "totalRevenue": total_revenue,
                    "newCustomers": new_customers,
                    "averageRating": round(avg_rating, 2),
                    "efficiency": round(efficiency, 1),
                    "profitMargin": profit_margin,
                    "completedOrders": completed_orders,
                    "inProgress": in_progress
                },
                "comparison": {
                    "ordersGrowth": round(orders_growth, 1),
                    "revenueGrowth": revenue_growth,
                    "customersGrowth": customers_growth,
                    "ratingGrowth": round(rating_growth, 1)
                }
            }
        }
        
    finally:
        db.close()

@router.get("/trends")
async def get_trends(
    period: str = Query("week", enum=["week", "month", "year"])
):
    """Получить тренды заявок"""
    db = SessionLocal()
    try:
        now = datetime.now()
        
        if period == "week":
            # Последние 7 дней
            labels = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
            values = []
            
            for i in range(7):
                date = (now - timedelta(days=6-i)).date()
                count = db.query(Ticket).filter(
                    func.date(Ticket.created_at) == date
                ).count()
                values.append(count)
                
        elif period == "month":
            # Последние 5 недель
            labels = ['1-7', '8-14', '15-21', '22-28', '29-31']
            values = []
            
            for i in range(5):
                start = now - timedelta(days=30 - i*7)
                end = start + timedelta(days=6)
                count = db.query(Ticket).filter(
                    Ticket.created_at.between(start, end)
                ).count()
                values.append(count)
                
        else:  # year
            # Последние 12 месяцев
            labels = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 
                     'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
            values = []
            
            for i in range(12):
                month = now.month - i
                year = now.year
                if month <= 0:
                    month += 12
                    year -= 1
                
                # Для MySQL используем EXTRACT или MONTH/YEAR
                count = db.query(Ticket).filter(
                    func.extract('year', Ticket.created_at) == year,
                    func.extract('month', Ticket.created_at) == month
                ).count()
                values.insert(0, count)
        
        return {
            "success": True,
            "data": {
                "labels": labels,
                "values": values
            }
        }
        
    finally:
        db.close()

@router.get("/orders-by-type")
async def get_orders_by_type():
    """Получить распределение заявок по категориям"""
    db = SessionLocal()
    try:
        # Группируем по категориям устройств
        categories = db.query(
            Ticket.category,
            func.count(Ticket.id).label('count')
        ).filter(
            Ticket.category.isnot(None),
            Ticket.category != ''
        ).group_by(Ticket.category).all()
        
        labels = []
        values = []
        colors = ['#2563EB', '#10B981', '#F59E0B', '#8B5CF6', '#EF4444', '#6B7280']
        
        for category in categories[:6]:  # Берем топ-6 категорий
            labels.append(category[0])
            values.append(category[1])
        
        # Если нет данных, добавляем заглушку
        if not labels:
            labels = ['Нет данных']
            values = [1]
        
        return {
            "success": True,
            "data": {
                "labels": labels,
                "values": values,
                "colors": colors[:len(labels)]
            }
        }
        
    finally:
        db.close()

@router.get("/masters-rating")
async def get_masters_rating(
    sort_by: str = Query("rating", enum=["rating", "orders", "revenue"])
):
    """Получить рейтинг мастеров"""
    db = SessionLocal()
    try:
        # У мастера нет поля is_active, используем status
        masters = db.query(Master).filter(
            Master.status == "active"
        ).all()
        
        if sort_by == "rating":
            masters.sort(key=lambda x: x.rating or 0, reverse=True)
        elif sort_by == "orders":
            masters.sort(key=lambda x: x.completed_orders or 0, reverse=True)
        else:  # revenue - приблизительный расчет
            masters.sort(key=lambda x: (x.completed_orders or 0) * 1000, reverse=True)
        
        labels = []
        values = []
        colors = ['#2563EB', '#10B981', '#F59E0B', '#8B5CF6', '#EF4444']
        
        for master in masters[:5]:
            name = f"{master.name} {master.surname[0]}." if master.surname else master.name
            labels.append(name)
            
            if sort_by == "rating":
                values.append(master.rating or 0)
            elif sort_by == "orders":
                values.append(master.completed_orders or 0)
            else:
                values.append((master.completed_orders or 0) * 1000)
        
        # Если нет мастеров, добавляем заглушку
        if not labels:
            labels = ['Нет данных']
            values = [0]
        
        return {
            "success": True,
            "data": {
                "labels": labels,
                "values": values,
                "colors": colors[:len(labels)]
            }
        }
        
    finally:
        db.close()

@router.get("/top-customers")
async def get_top_customers(limit: int = 5):
    """Получить топ клиентов по количеству заявок"""
    db = SessionLocal()
    try:
        # Получаем клиентов с количеством заявок
        customers = db.query(
            Client,
            func.count(Ticket.id).label('ticket_count')
        ).join(
            Ticket, Ticket.client_id == Client.id, isouter=True
        ).group_by(
            Client.id
        ).order_by(
            func.count(Ticket.id).desc()
        ).limit(limit).all()
        
        result = []
        for client, ticket_count in customers:
            # Приблизительная выручка
            revenue = ticket_count * 1000
            trend = "up" if ticket_count > 5 else "stable" if ticket_count > 2 else "down"
            
            result.append({
                "name": client.name or f"Клиент #{client.id}",
                "orders": ticket_count,
                "revenue": revenue,
                "trend": trend
            })
        
        return {
            "success": True,
            "data": result
        }
        
    finally:
        db.close()

@router.get("/weekday-stats")
async def get_weekday_stats():
    """Получить статистику по дням недели"""
    db = SessionLocal()
    try:
        days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        result = []
        
        for i, day in enumerate(days, 1):
            # Для MySQL/MariaDB используем DAYOFWEEK()
            # DAYOFWEEK() возвращает 1 = воскресенье, 2 = понедельник, ..., 7 = суббота
            # Нам нужно: 1 = понедельник, 2 = вторник, ..., 7 = воскресенье
            # Поэтому делаем преобразование
            mysql_weekday = i + 1  # преобразуем наш формат (1=пн) в MySQL DAYOFWEEK (2=пн)
            if mysql_weekday > 7:
                mysql_weekday = 1  # воскресенье = 1
                
            tickets = db.query(Ticket).filter(
                func.dayofweek(Ticket.created_at) == mysql_weekday
            ).all()
            
            orders = len(tickets)
            revenue = orders * 1000  # Заглушка
            avg_time = f"{2 + i % 3}.{i % 2 * 5}ч"
            
            # Считаем процент от общего количества
            total_orders = db.query(Ticket).count()
            percentage = (orders / total_orders * 100) if total_orders > 0 else 0
            
            result.append({
                "day": day,
                "orders": orders,
                "revenue": revenue,
                "avgTime": avg_time,
                "percentage": round(percentage, 1)
            })
        
        # Сортируем по дням недели (пн-вс)
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        print(f"Error in get_weekday_stats: {e}")
        # Возвращаем пустые данные в случае ошибки
        return {
            "success": True,
            "data": [
                {"day": "Понедельник", "orders": 0, "revenue": 0, "avgTime": "0ч", "percentage": 0},
                {"day": "Вторник", "orders": 0, "revenue": 0, "avgTime": "0ч", "percentage": 0},
                {"day": "Среда", "orders": 0, "revenue": 0, "avgTime": "0ч", "percentage": 0},
                {"day": "Четверг", "orders": 0, "revenue": 0, "avgTime": "0ч", "percentage": 0},
                {"day": "Пятница", "orders": 0, "revenue": 0, "avgTime": "0ч", "percentage": 0},
                {"day": "Суббота", "orders": 0, "revenue": 0, "avgTime": "0ч", "percentage": 0},
                {"day": "Воскресенье", "orders": 0, "revenue": 0, "avgTime": "0ч", "percentage": 0}
            ]
        }
    finally:
        db.close()
@router.get("/comparison")
async def get_comparison(
    period: str = Query("month", enum=["month", "quarter", "year"])
):
    """Получить сравнение с предыдущим периодом"""
    db = SessionLocal()
    try:
        now = datetime.now()
        
        if period == "month":
            days = 30
        elif period == "quarter":
            days = 90
        else:  # year
            days = 365
        
        # Текущий период
        current_start = now - timedelta(days=days)
        current_end = now
        
        # Предыдущий период
        prev_start = current_start - timedelta(days=days)
        prev_end = current_end - timedelta(days=days)
        
        # Текущие показатели
        current_orders = db.query(Ticket).filter(
            Ticket.created_at.between(current_start, current_end)
        ).count()
        
        current_revenue = 0  # Заглушка
        
        current_customers = db.query(Client).filter(
            Client.created_at.between(current_start, current_end)
        ).count()
        
        current_avg_rating = db.query(func.avg(Master.rating)).scalar() or 0
        
        # Предыдущие показатели
        prev_orders = db.query(Ticket).filter(
            Ticket.created_at.between(prev_start, prev_end)
        ).count()
        
        prev_revenue = 0  # Заглушка
        
        prev_customers = db.query(Client).filter(
            Client.created_at.between(prev_start, prev_end)
        ).count()
        
        prev_avg_rating = db.query(func.avg(Master.rating)).scalar() or 0
        
        # Расчет времени ремонта (заглушка)
        repair_time_current = 2.4
        repair_time_prev = 2.6
        
        comparison = [
            {
                "title": "Выручка",
                "current": current_revenue,
                "previous": prev_revenue,
                "change": round(((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0, 1)
            },
            {
                "title": "Количество заявок",
                "current": current_orders,
                "previous": prev_orders,
                "change": round(((current_orders - prev_orders) / prev_orders * 100) if prev_orders > 0 else 0, 1)
            },
            {
                "title": "Новые клиенты",
                "current": current_customers,
                "previous": prev_customers,
                "change": round(((current_customers - prev_customers) / prev_customers * 100) if prev_customers > 0 else 0, 1)
            },
            {
                "title": "Средний чек",
                "current": 0,
                "previous": 0,
                "change": 0
            },
            {
                "title": "Время ремонта",
                "current": repair_time_current,
                "previous": repair_time_prev,
                "change": round((repair_time_current - repair_time_prev) / repair_time_prev * 100, 1)
            },
            {
                "title": "Удовлетворенность",
                "current": round(current_avg_rating, 2),
                "previous": round(prev_avg_rating, 2),
                "change": round((current_avg_rating - prev_avg_rating) / prev_avg_rating * 100, 1) if prev_avg_rating > 0 else 0
            }
        ]
        
        return {
            "success": True,
            "data": comparison
        }
        
    finally:
        db.close()

@router.get("/parts-stats")
async def get_parts_statistics():
    """Получить статистику по запчастям"""
    db = SessionLocal()
    try:
        # Общая статистика по запчастям
        total_parts = db.query(Part).count()
        total_stock = db.query(func.sum(Part.stock)).scalar() or 0
        total_value = db.query(func.sum(Part.purchase_price * Part.stock)).scalar() or 0
        low_stock = db.query(Part).filter(
            Part.stock < Part.min_stock
        ).count()
        
        # Статистика по категориям
        from app.models.part import PartCategory
        categories = db.query(PartCategory).all()
        categories_stats = []
        
        for cat in categories:
            cat_parts = db.query(Part).filter(Part.category_id == cat.id).count()
            cat_value = db.query(func.sum(Part.purchase_price * Part.stock)).filter(
                Part.category_id == cat.id
            ).scalar() or 0
            
            categories_stats.append({
                "id": cat.id,
                "name": cat.name,
                "count": cat_parts,
                "total_value": float(cat_value)
            })
        
        return {
            "success": True,
            "data": {
                "total_parts": total_parts,
                "total_stock": total_stock,
                "total_value": float(total_value),
                "low_stock": low_stock,
                "categories": categories_stats
            }
        }
        
    finally:
        db.close()