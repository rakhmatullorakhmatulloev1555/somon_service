from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

import app.bot.services.ticket_service as ticket_service

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


# ---------- DASHBOARD ----------

@router.get("/admin")
async def admin_dashboard(request: Request):

    tickets = ticket_service.get_all_tickets()

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "tickets": tickets
        }
    )


# ---------- TICKET PAGE ----------

@router.get("/admin/ticket/{ticket_id}")
async def ticket_detail(request: Request, ticket_id: int):

    ticket = ticket_service.get_ticket(ticket_id)

    return templates.TemplateResponse(
        "admin/ticket.html",
        {
            "request": request,
            "ticket": ticket
        }
    )


# ---------- CHANGE STATUS ----------

@router.post("/admin/status/{ticket_id}")
async def change_status(ticket_id: int, status: str = Form(...)):

    ticket_service.update_status(ticket_id, status)

    return RedirectResponse(
        f"/admin/ticket/{ticket_id}",
        status_code=303
    )
