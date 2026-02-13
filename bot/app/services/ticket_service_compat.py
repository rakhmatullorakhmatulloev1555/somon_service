# app/services/ticket_service_compat.py
"""
Сервис для совместимости с веб-админкой
"""
from app.database import SessionLocal
from app.models.ticket import Ticket, DeliveryMethod
from app.models.master import Master
from app.models.client import Client
from sqlalchemy.orm import joinedload
import json
from datetime import datetime

# ========================
# ФУНКЦИИ ДЛЯ ВЕБ-АДМИНКИ
# ========================

def get_all_tickets():
    """Получить все заявки (старый формат для веб-админки)"""
    db = SessionLocal()
    try:
        tickets = db.query(Ticket).options(
            joinedload(Ticket.client),
            joinedload(Ticket.master)
        ).order_by(Ticket.created_at.desc()).all()
        
        result = []
        for ticket in tickets:
            # Определяем имя клиента
            client_name = ""
            if ticket.client:
                client_name = ticket.client.name or ""
            elif ticket.walkin_name:
                client_name = ticket.walkin_name
            
            # Определяем телефон
            client_phone = ""
            if ticket.client and ticket.client.phone:
                client_phone = ticket.client.phone
            elif ticket.walkin_phone:
                client_phone = ticket.walkin_phone
            
            # Определяем способ получения
            delivery_method_text = {
                DeliveryMethod.PICKUP.value: "Самовывоз",
                DeliveryMethod.DELIVERY.value: "Доставка",
                DeliveryMethod.WALKIN.value: "В сервисе"
            }.get(ticket.delivery_method, "Не указан")
            
            result.append({
                "id": ticket.id,
                "client_name": client_name,
                "client_phone": client_phone,
                "delivery_method": delivery_method_text,
                "category": ticket.category or "",
                "brand": ticket.brand or "",
                "problem": ticket.problem or "",
                "status": ticket.status or "Новая",
                "master_name": ticket.master.name if ticket.master else "Не назначен",
                "created_at": ticket.created_at.strftime("%d.%m.%Y %H:%M") if ticket.created_at else "",
                # Добавляем все поля для веб-админки
                "client_id": ticket.client_id,
                "master_id": ticket.master_id,
                "branch": ticket.branch or "",
                "subcategory": ticket.subcategory or "",
                "urgency": ticket.urgency or "",
                "photos": json.loads(ticket.photos) if ticket.photos else [],
                "delivery_address": ticket.delivery_address or "",
                "delivery_phone": ticket.delivery_phone or "",
                "delivery_date": str(ticket.delivery_date) if ticket.delivery_date else "",
                "delivery_notes": ticket.delivery_notes or "",
                "walkin_name": ticket.walkin_name or "",
                "walkin_phone": ticket.walkin_phone or "",
                "client_telegram_id": ticket.client.telegram_id if ticket.client else None
            })
        
        return result
        
    except Exception as e:
        print(f"Error getting all tickets: {e}")
        return []
    finally:
        db.close()

def get_ticket(ticket_id):
    """Получить заявку по ID (старый формат)"""
    db = SessionLocal()
    try:
        ticket = db.query(Ticket).options(
            joinedload(Ticket.client),
            joinedload(Ticket.master)
        ).filter(Ticket.id == ticket_id).first()
        
        if not ticket:
            return None
        
        # Определяем имя клиента
        client_name = ""
        if ticket.client:
            client_name = ticket.client.name or ""
        elif ticket.walkin_name:
            client_name = ticket.walkin_name
        
        # Определяем телефон
        client_phone = ""
        if ticket.client and ticket.client.phone:
            client_phone = ticket.client.phone
        elif ticket.walkin_phone:
            client_phone = ticket.walkin_phone
        
        return {
            "id": ticket.id,
            "client_name": client_name,
            "client_phone": client_phone,
            "client_telegram_id": ticket.client.telegram_id if ticket.client else None,
            "master_id": ticket.master_id,
            "status": ticket.status or "Новая",
            "category": ticket.category or "",
            "brand": ticket.brand or "",
            "problem": ticket.problem or "",
            "branch": ticket.branch or ""
        }
        
    except Exception as e:
        print(f"Error getting ticket {ticket_id}: {e}")
        return None
    finally:
        db.close()

def update_status(ticket_id, status):
    """Обновить статус заявки"""
    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket:
            ticket.status = status
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Error updating status: {e}")
        return False
    finally:
        db.close()

def assign_master(ticket_id, master_id):
    """Назначить мастера на заявку"""
    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket:
            ticket.master_id = master_id
            ticket.status = "В работе"
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Error assigning master: {e}")
        return False
    finally:
        db.close()

def get_all_masters():
    """Получить всех мастеров"""
    db = SessionLocal()
    try:
        masters = db.query(Master).all()
        result = []
        for m in masters:
            result.append({
                "id": m.id,
                "name": m.name,
                "surname": m.surname or "",
                "telegram_id": m.telegram_id or "",
                "phone": m.phone or "",
                "specialization": m.specialization or "",
                "experience": m.experience or 0,
                "rating": m.rating or 0,
                "rating_count": m.rating_count or 0,
                "status": m.status or "active",
                "completed_orders": m.completed_orders or 0,
                "active_orders": m.active_orders or 0
            })
        return result
    except Exception as e:
        print(f"Error getting masters: {e}")
        return []
    finally:
        db.close()

def get_statistics():
    """Получить статистику"""
    db = SessionLocal()
    try:
        total_tickets = db.query(Ticket).count()
        new_tickets = db.query(Ticket).filter(Ticket.status == "Новая").count()
        in_progress = db.query(Ticket).filter(Ticket.status.in_(["В работе", "🧪 Диагностика", "🔧 В ремонте"])).count()
        completed = db.query(Ticket).filter(Ticket.status == "✅ Готово").count()
        
        total_masters = db.query(Master).count()
        active_masters = db.query(Master).filter(Master.status == "active").count()
        
        # Статистика за сегодня
        today = datetime.now().date()
        today_tickets = db.query(Ticket).filter(
            db.func.date(Ticket.created_at) == today
        ).count()
        
        # Статистика по филиалам
        branches = db.query(Ticket.branch).distinct().all()
        branch_stats = {}
        for branch in branches:
            if branch[0]:
                count = db.query(Ticket).filter(Ticket.branch == branch[0]).count()
                branch_stats[branch[0]] = count
        
        return {
            "tickets": {
                "total": total_tickets,
                "new": new_tickets,
                "in_progress": in_progress,
                "completed": completed,
                "today": today_tickets
            },
            "masters": {
                "total": total_masters,
                "active": active_masters
            },
            "branches": branch_stats
        }
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return {"tickets": {}, "masters": {}, "branches": {}}
    finally:
        db.close()