# app/services/event_service.py
from app.database import SessionLocal
from app.models.event import Event
from app.models.master import Master
from app.models.client import Client
from app.models.ticket import Ticket
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
import logging

logger = logging.getLogger(__name__)

def create_event(data: dict):
    """Создать новое событие"""
    db = SessionLocal()
    try:
        event = Event(
            title=data.get("title"),
            event_type=data.get("event_type"),
            color=data.get("color", "primary"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            is_all_day=data.get("is_all_day", False),
            master_id=data.get("master_id"),
            client_id=data.get("client_id"),
            ticket_id=data.get("ticket_id"),
            description=data.get("description"),
            location=data.get("location"),
            reminder_minutes=data.get("reminder_minutes", 30),
            created_by=data.get("created_by")
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating event: {e}")
        raise
    finally:
        db.close()

def get_events(start_date: datetime = None, end_date: datetime = None):
    """Получить события за период"""
    db = SessionLocal()
    try:
        query = db.query(Event)
        
        if start_date:
            query = query.filter(Event.start_date >= start_date)
        if end_date:
            query = query.filter(Event.start_date <= end_date)
        
        return query.order_by(Event.start_date).all()
    finally:
        db.close()

def get_event(event_id: int):
    """Получить событие по ID"""
    db = SessionLocal()
    try:
        return db.query(Event).filter(Event.id == event_id).first()
    finally:
        db.close()

def update_event(event_id: int, data: dict):
    """Обновить событие"""
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            return None
        
        for key, value in data.items():
            if hasattr(event, key):
                setattr(event, key, value)
        
        db.commit()
        db.refresh(event)
        return event
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating event {event_id}: {e}")
        raise
    finally:
        db.close()

def delete_event(event_id: int):
    """Удалить событие"""
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if event:
            db.delete(event)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting event {event_id}: {e}")
        raise
    finally:
        db.close()

def get_master_events(master_id: int, start_date: datetime = None, end_date: datetime = None):
    """Получить события конкретного мастера"""
    db = SessionLocal()
    try:
        query = db.query(Event).filter(Event.master_id == master_id)
        
        if start_date:
            query = query.filter(Event.start_date >= start_date)
        if end_date:
            query = query.filter(Event.start_date <= end_date)
        
        return query.order_by(Event.start_date).all()
    finally:
        db.close()

def get_events_for_notification():
    """Получить события, по которым нужно отправить уведомления"""
    db = SessionLocal()
    try:
        now = datetime.now()
        reminder_time = now + timedelta(minutes=30)
        
        events = db.query(Event).filter(
            and_(
                Event.notification_sent == False,
                Event.start_date <= reminder_time,
                Event.start_date >= now
            )
        ).all()
        
        return events
    finally:
        db.close()

def create_event_from_ticket(ticket_id: int, master_id: int = None):
    """Автоматически создать событие на основе заявки"""
    db = SessionLocal()
    try:
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            return None
        
        event = Event(
            title=f"Ремонт {ticket.brand} - #{ticket.id}",
            event_type="repair",
            color="primary",
            start_date=ticket.created_at + timedelta(hours=1),
            end_date=ticket.created_at + timedelta(hours=3),
            master_id=master_id,
            client_id=ticket.client_id,
            ticket_id=ticket.id,
            description=ticket.problem,
            location=f"Филиал: {ticket.branch}",
            reminder_minutes=30
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating event from ticket: {e}")
        return None
    finally:
        db.close()