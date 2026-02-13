from fastapi import APIRouter
import app.bot.services.ticket_service as ticket_service

router = APIRouter(prefix="/api")

@router.get("/tickets")
async def get_tickets():
    return ticket_service.get_all_tickets()
