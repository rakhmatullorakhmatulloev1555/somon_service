# app/api/admin_api.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.ticket_service_compat import (
    get_all_tickets,
    get_ticket,
    update_status,
    assign_master,
    get_all_masters,
    get_statistics
)

router = APIRouter(prefix="/api/admin")

# Модели для запросов
class StatusUpdate(BaseModel):
    status: str

class MasterAssign(BaseModel):
    master_id: int

class TicketFilter(BaseModel):
    status: Optional[str] = None
    master_id: Optional[int] = None
    branch: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None

# Эндпоинты для заявок
@router.get("/tickets")
async def get_tickets():
    """Получить все заявки"""
    tickets = get_all_tickets()
    return {"success": True, "data": tickets}

@router.get("/tickets/{ticket_id}")
async def get_ticket_by_id(ticket_id: int):
    """Получить заявку по ID"""
    ticket = get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return {"success": True, "data": ticket}

@router.put("/tickets/{ticket_id}/status")
async def update_ticket_status(ticket_id: int, status_data: StatusUpdate):
    """Обновить статус заявки"""
    success = update_status(ticket_id, status_data.status)
    if not success:
        raise HTTPException(status_code=400, detail="Не удалось обновить статус")
    return {"success": True, "message": "Статус обновлен"}

@router.put("/tickets/{ticket_id}/master")
async def assign_ticket_master(ticket_id: int, master_data: MasterAssign):
    """Назначить мастера на заявку"""
    success = assign_master(ticket_id, master_data.master_id)
    if not success:
        raise HTTPException(status_code=400, detail="Не удалось назначить мастера")
    return {"success": True, "message": "Мастер назначен"}

# Эндпоинты для мастеров
@router.get("/masters")
async def get_masters():
    """Получить всех мастеров"""
    masters = get_all_masters()
    return {"success": True, "data": masters}

@router.get("/masters/{master_id}")
async def get_master_by_id(master_id: int):
    """Получить мастера по ID"""
    masters = get_all_masters()
    master = next((m for m in masters if m["id"] == master_id), None)
    if not master:
        raise HTTPException(status_code=404, detail="Мастер не найден")
    return {"success": True, "data": master}

# Эндпоинты для статистики
@router.get("/statistics")
async def get_admin_statistics():
    """Получить статистику"""
    stats = get_statistics()
    return {"success": True, "data": stats}

# Эндпоинты для клиентов
@router.get("/clients")
async def get_clients():
    """Получить всех клиентов"""
    from app.models.client import Client
    from app.models.ticket import Ticket
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        clients = db.query(Client).all()
        result = []
        for c in clients:
            # Используем отдельный запрос для подсчета, не обращаемся к c.tickets
            ticket_count = db.query(Ticket).filter(Ticket.client_id == c.id).count()
            
            result.append({
                "id": c.id,
                "name": c.name or "Без имени",
                "phone": c.phone or "Не указан",
                "telegram_id": c.telegram_id,
                "username": c.username,
                "full_name": c.name,
                "loyalty": "medium",  # Заглушка
                "created_at": c.created_at.isoformat() if c.created_at else "",
                "ticket_count": ticket_count
            })
        return {"success": True, "data": result}
    finally:
        db.close()

# Фильтрация заявок
@router.post("/tickets/filter")
async def filter_tickets(filter_data: TicketFilter):
    """Фильтрация заявок"""
    from app.database import SessionLocal
    from app.models.ticket import Ticket
    from sqlalchemy.orm import joinedload
    from datetime import datetime
    
    db = SessionLocal()
    try:
        query = db.query(Ticket).options(
            joinedload(Ticket.client),
            joinedload(Ticket.master)
        )
        
        # Применяем фильтры
        if filter_data.status:
            query = query.filter(Ticket.status == filter_data.status)
        
        if filter_data.master_id:
            query = query.filter(Ticket.master_id == filter_data.master_id)
        
        if filter_data.branch:
            query = query.filter(Ticket.branch == filter_data.branch)
        
        if filter_data.date_from:
            try:
                date_from = datetime.fromisoformat(filter_data.date_from)
                query = query.filter(Ticket.created_at >= date_from)
            except:
                pass
        
        if filter_data.date_to:
            try:
                date_to = datetime.fromisoformat(filter_data.date_to)
                query = query.filter(Ticket.created_at <= date_to)
            except:
                pass
        
        tickets = query.order_by(Ticket.created_at.desc()).all()
        
        # Форматируем результат
        result = []
        for ticket in tickets:
            result.append({
                "id": ticket.id,
                "client_name": ticket.client.name if ticket.client else ticket.walkin_name or "Клиент",
                "client_phone": ticket.client.phone if ticket.client else ticket.walkin_phone or "",
                "status": ticket.status,
                "master_name": ticket.master.name if ticket.master else "Не назначен",
                "category": ticket.category or "",
                "brand": ticket.brand or "",
                "created_at": ticket.created_at.isoformat() if ticket.created_at else "",
                "branch": ticket.branch or ""
            })
        
        return {"success": True, "data": result}
        
    finally:
        db.close()