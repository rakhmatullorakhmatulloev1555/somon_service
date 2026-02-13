# app/bot/services/ticket_service.py
from app.database import SessionLocal
from app.models.ticket import Ticket, DeliveryMethod
from app.models.master import Master
from app.services.client_service import get_or_create_client
from app.bot.loader import bot
from sqlalchemy.orm import joinedload
import json
from datetime import datetime

GROUP_ID = -1003664975361

def create_ticket(data, telegram_user=None):
    """Создание заявки для всех 3 способов"""
    db = SessionLocal()
    try:
        # Для клиентов из Telegram
        if telegram_user:
            client = get_or_create_client(db, telegram_user)
            client_id = client.id
            walkin_name = None
            walkin_phone = None
        else:
            # Для клиентов без Telegram (walk-in)
            client_id = None
            walkin_name = data.get("walkin_name")
            walkin_phone = data.get("walkin_phone")
        
        # Создаем заявку
        ticket = Ticket(
            client_id=client_id,
            delivery_method=DeliveryMethod(data.get("delivery_method", DeliveryMethod.PICKUP.value)),
            
            # Поля для доставки
            delivery_address=data.get("delivery_address"),
            delivery_phone=data.get("delivery_phone"),
            delivery_date=data.get("delivery_date"),
            delivery_notes=data.get("delivery_notes"),
            
            # Поля для walk-in клиентов
            walkin_name=walkin_name,
            walkin_phone=walkin_phone,
            
            # Общие поля
            branch=data.get("branch"),
            category=data.get("category"),
            subcategory=data.get("subcategory"),
            brand=data.get("brand"),
            problem=data.get("problem"),
            urgency=data.get("urgency"),
            status="Новая",
            photos=json.dumps(data.get("photos", [])),
            created_at=datetime.now()
        )
        
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        return ticket.id
        
    except Exception as e:
        db.rollback()
        print(f"Error creating ticket: {e}")
        raise
    finally:
        db.close()

def get_ticket(ticket_id: int):
    """Получить заявку по ID"""
    db = SessionLocal()
    try:
        ticket = db.query(Ticket).options(
            joinedload(Ticket.client),
            joinedload(Ticket.master)
        ).filter(Ticket.id == ticket_id).first()
        return ticket
    except Exception as e:
        print(f"Error getting ticket {ticket_id}: {e}")
        return None
    finally:
        db.close()

def update_ticket_status(ticket_id: int, new_status: str):
    """Обновить статус заявки"""
    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket:
            ticket.status = new_status
            if new_status == "✅ Готово":
                ticket.completed_at = datetime.now()
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Error updating ticket status: {e}")
        return False
    finally:
        db.close()

def assign_master(ticket_id: int, master_telegram_id: int):
    """Назначить мастера на заявку"""
    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        master = db.query(Master).filter(Master.telegram_id == str(master_telegram_id)).first()
        
        if ticket and master:
            ticket.master_id = master.id
            ticket.status = "🧪 Диагностика"
            db.commit()
            return True, ticket, master
        return False, None, None
    except Exception as e:
        db.rollback()
        print(f"Error assigning master: {e}")
        return False, None, None
    finally:
        db.close()

def create_walkin_ticket(client_name: str, client_phone: str, branch: str, 
                         category: str, brand: str, problem: str):
    """Создание заявки для клиента без предварительной заявки"""
    db = SessionLocal()
    try:
        ticket = Ticket(
            delivery_method=DeliveryMethod.WALKIN.value,
            walkin_name=client_name,
            walkin_phone=client_phone,
            branch=branch,
            category=category,
            brand=brand,
            problem=problem,
            status="Новая",
            urgency="🔵 Обычная",
            created_at=datetime.now()
        )
        
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        return ticket.id
        
    except Exception as e:
        db.rollback()
        print(f"Error creating walk-in ticket: {e}")
        raise
    finally:
        db.close()

def get_all_tickets_with_details():
    """Получить все заявки с деталями"""
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
                client_name = ticket.client.name or "Клиент"
            elif ticket.walkin_name:
                client_name = ticket.walkin_name
            
            # Определяем телефон
            client_phone = ""
            if ticket.client and ticket.client.phone:
                client_phone = ticket.client.phone
            elif ticket.walkin_phone:
                client_phone = ticket.walkin_phone
            elif ticket.delivery_phone:
                client_phone = ticket.delivery_phone
            
            # Определяем способ получения
            delivery_method_text = {
                DeliveryMethod.PICKUP.value: "🚶 Самовывоз",
                DeliveryMethod.DELIVERY.value: "🚚 Доставка",
                DeliveryMethod.WALKIN.value: "🏪 В сервисе"
            }.get(ticket.delivery_method, "Не указан")
            
            result.append({
                "id": ticket.id,
                "client_name": client_name,
                "client_phone": client_phone,
                "delivery_method": delivery_method_text,
                "category": ticket.category,
                "brand": ticket.brand,
                "problem": ticket.problem[:50] + "..." if ticket.problem and len(ticket.problem) > 50 else ticket.problem or "",
                "status": ticket.status,
                "master_name": ticket.master.name if ticket.master else "Не назначен",
                "master_id": ticket.master.id if ticket.master else None,
                "created_at": ticket.created_at.strftime("%d.%m.%Y %H:%M") if ticket.created_at else ""
            })
        
        return result
        
    except Exception as e:
        print(f"Error getting tickets: {e}")
        return []
    finally:
        db.close()

def get_client_tickets(client_telegram_id: int):
    """Получить заявки клиента по его Telegram ID"""
    db = SessionLocal()
    try:
        from app.models.client import Client
        client = db.query(Client).filter(Client.telegram_id == str(client_telegram_id)).first()
        
        if not client:
            return []
        
        tickets = db.query(Ticket).filter(
            Ticket.client_id == client.id
        ).order_by(Ticket.created_at.desc()).all()
        
        return tickets
    except Exception as e:
        print(f"Error getting client tickets: {e}")
        return []
    finally:
        db.close()

def get_active_tickets():
    """Получить активные заявки (не завершенные)"""
    db = SessionLocal()
    try:
        tickets = db.query(Ticket).filter(
            Ticket.status != "✅ Готово"
        ).order_by(Ticket.created_at.desc()).all()
        return tickets
    except Exception as e:
        print(f"Error getting active tickets: {e}")
        return []
    finally:
        db.close()

def get_ticket_by_id(ticket_id: int):
    """Альтернативное название для get_ticket"""
    return get_ticket(ticket_id)

# app/bot/services/ticket_service.py
# Добавьте эту функцию после существующих функций

def assign_master_by_telegram(ticket_id: int, master_telegram_id: int):
    """Назначить мастера на заявку по Telegram ID"""
    db = SessionLocal()
    try:
        # Находим заявку
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return False, "Заявка не найдена"
        
        # Проверяем, не назначен ли уже мастер
        if ticket.master_id:
            # Получаем имя уже назначенного мастера
            current_master = db.query(Master).filter(Master.id == ticket.master_id).first()
            master_name = current_master.name if current_master else "Неизвестно"
            return False, f"На эту заявку уже назначен мастер ({master_name})"
        
        # Находим мастера по Telegram ID
        master = db.query(Master).filter(Master.telegram_id == str(master_telegram_id)).first()
        if not master:
            return False, "Мастер не найден в базе данных"
        
        # Назначаем мастера
        ticket.master_id = master.id
        ticket.status = "🧪 Диагностика"
        
        # Увеличиваем счетчик активных заказов у мастера
        master.active_orders = (master.active_orders or 0) + 1
        
        db.commit()
        db.refresh(ticket)
        
        return True, f"Мастер {master.name} назначен на заявку #{ticket_id}"
        
    except Exception as e:
        db.rollback()
        print(f"Error assigning master by telegram: {e}")
        return False, f"Ошибка: {str(e)}"
    finally:
        db.close()
def update_status(ticket_id: int, new_status: str):
    """Обновить статус заявки"""
    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return False
        
        ticket.status = new_status
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        print(f"Error updating ticket status: {e}")
        return False
    finally:
        db.close()        