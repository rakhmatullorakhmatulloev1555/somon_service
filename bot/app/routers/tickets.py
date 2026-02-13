# app/routers/tickets.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.ticket import Ticket, DeliveryMethod
from app.models.client import Client
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse  # Добавьте этот импорт


router = APIRouter(prefix="/api", tags=["tickets"])
templates = Jinja2Templates(directory="app/templates")

class WalkinTicketCreate(BaseModel):
    client_name: str
    client_phone: str
    branch: str
    category: str
    brand: str
    problem: str
    urgency: str = "⏳ Обычная"

@router.post("/walkin-tickets")
async def create_walkin_ticket_web(
    ticket_data: WalkinTicketCreate,
    db: Session = Depends(get_db)
):
    """Создание заявки для клиента в сервисе (без предварительной заявки)"""
    try:
        ticket = Ticket(
            delivery_method=DeliveryMethod.WALKIN.value,
            walkin_name=ticket_data.client_name,
            walkin_phone=ticket_data.client_phone,
            branch=ticket_data.branch,
            category=ticket_data.category,
            brand=ticket_data.brand,
            problem=ticket_data.problem,
            urgency=ticket_data.urgency,
            status="Новая"
        )
        
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        # Здесь можно добавить уведомление в Telegram
        
        return {
            "success": True,
            "ticket_id": ticket.id,
            "message": f"Заявка #{ticket.id} создана для клиента в сервисе"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/admin/walkin", response_class=HTMLResponse)
async def walkin_ticket_page(request: Request):
    """Страница создания заявки для клиента в сервисе"""
    return templates.TemplateResponse(
        "admin/walkin_ticket.html",
        {"request": request}
    )

# Оставьте существующий код если есть
@router.get("/tickets")
def get_tickets(db: Session = Depends(get_db)):
    tickets = db.query(Ticket).all()

    return [
        {
            "id": t.id,
            "title": t.problem,
            "device": t.brand,
            "client": t.client_id,
            "status": t.status,
            "created_at": t.created_at
        }
        for t in tickets
    ]
