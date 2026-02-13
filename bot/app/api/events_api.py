# app/api/events_api.py
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional, List
from app.services import event_service
from app.database import SessionLocal
from app.models.master import Master
from app.models.client import Client

router = APIRouter(prefix="/api/events")

class EventCreate(BaseModel):
    title: str
    event_type: str
    color: Optional[str] = "primary"
    start_date: datetime
    end_date: Optional[datetime] = None
    is_all_day: bool = False
    master_id: Optional[int] = None
    client_id: Optional[int] = None
    ticket_id: Optional[int] = None
    description: Optional[str] = None
    location: Optional[str] = None
    reminder_minutes: int = 30

class EventUpdate(BaseModel):
    title: Optional[str] = None
    event_type: Optional[str] = None
    color: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_all_day: Optional[bool] = None
    master_id: Optional[int] = None
    client_id: Optional[int] = None
    ticket_id: Optional[int] = None
    description: Optional[str] = None
    location: Optional[str] = None
    reminder_minutes: Optional[int] = None

@router.get("")
async def get_events(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    master_id: Optional[int] = Query(None)
):
    """Получить события"""
    try:
        start = datetime.fromisoformat(start_date) if start_date else datetime.now().replace(day=1)
        end = datetime.fromisoformat(end_date) if end_date else start + timedelta(days=30)
    except:
        start = datetime.now().replace(day=1)
        end = start + timedelta(days=30)
    
    if master_id:
        events = event_service.get_master_events(master_id, start, end)
    else:
        events = event_service.get_events(start, end)
    
    result = []
    for e in events:
        result.append({
            "id": e.id,
            "title": e.title,
            "type": e.event_type,
            "color": e.color,
            "start": e.start_date.isoformat(),
            "end": e.end_date.isoformat() if e.end_date else None,
            "is_all_day": e.is_all_day,
            "master_id": e.master_id,
            "master_name": e.master.name if e.master else None,
            "client_id": e.client_id,
            "client_name": e.client.name if e.client else None,
            "ticket_id": e.ticket_id,
            "description": e.description,
            "location": e.location
        })
    
    return {"success": True, "data": result}

@router.get("/{event_id}")
async def get_event(event_id: int):
    """Получить событие по ID"""
    event = event_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    
    return {
        "success": True,
        "data": {
            "id": event.id,
            "title": event.title,
            "type": event.event_type,
            "color": event.color,
            "start": event.start_date.isoformat(),
            "end": event.end_date.isoformat() if event.end_date else None,
            "is_all_day": event.is_all_day,
            "master_id": event.master_id,
            "master_name": event.master.name if event.master else None,
            "client_id": event.client_id,
            "client_name": event.client.name if event.client else None,
            "ticket_id": event.ticket_id,
            "description": event.description,
            "location": event.location,
            "reminder_minutes": event.reminder_minutes
        }
    }

@router.post("")
async def create_event(event_data: EventCreate):
    """Создать новое событие"""
    try:
        event = event_service.create_event(event_data.dict())
        return {
            "success": True,
            "message": "Событие создано",
            "id": event.id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{event_id}")
async def update_event(event_id: int, event_data: EventUpdate):
    """Обновить событие"""
    event = event_service.update_event(event_id, event_data.dict(exclude_unset=True))
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    
    return {
        "success": True,
        "message": "Событие обновлено"
    }

@router.delete("/{event_id}")
async def delete_event(event_id: int):
    """Удалить событие"""
    success = event_service.delete_event(event_id)
    if not success:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    
    return {
        "success": True,
        "message": "Событие удалено"
    }

@router.post("/from-ticket/{ticket_id}")
async def create_event_from_ticket(ticket_id: int, master_id: Optional[int] = None):
    """Создать событие из заявки"""
    event = event_service.create_event_from_ticket(ticket_id, master_id)
    if not event:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    return {
        "success": True,
        "message": "Событие создано из заявки",
        "id": event.id
    }