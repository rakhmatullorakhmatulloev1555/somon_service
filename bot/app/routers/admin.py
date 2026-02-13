from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse


router = APIRouter(prefix="/admin")

templates = Jinja2Templates(directory="app/templates")

@router.get("/admin")
async def admin_panel(request: Request):

    if not request.session.get("user"):
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/login")

    return templates.TemplateResponse(
        "/admin/dashboard.html",
        {"request": request}
    )
@router.get("/orders", response_class=HTMLResponse)
async def orders_page(request: Request):
    return templates.TemplateResponse(
        "admin/orders.html",
        {"request": request}
    )

@router.get("/calendar", response_class=HTMLResponse)
async def calendar_page(request: Request):

    return templates.TemplateResponse(
        "admin/calendar.html",
        {"request": request}
    )

@router.get("/clients", response_class=HTMLResponse)
async def clients_page(request: Request):

    return templates.TemplateResponse(
        "admin/clients.html",
        {"request": request}
    )
@router.get("/masters", response_class=HTMLResponse)
async def masters_page(request: Request):

    return templates.TemplateResponse(
        "admin/masters.html",
        {"request": request}
    )
@router.get("/parts", response_class=HTMLResponse)
async def parts_page(request: Request):

    return templates.TemplateResponse(
        "admin/parts.html",
        {"request": request}
    )

@router.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):   

    return templates.TemplateResponse(
        "admin/reports.html",
        {"request": request}
    )
    
@router.get("/finances", response_class=HTMLResponse)            
async def finances_page(request: Request):

    return templates.TemplateResponse(
        "admin/finances.html",
        {"request": request}
    )
@router.get("/statistics", response_class=HTMLResponse)
async def statistics_page(request: Request):

    return templates.TemplateResponse(
        "admin/statistics.html",
        {"request": request}
    )

@router.get("/botsettings", response_class=HTMLResponse)
async def botsettings_page(request: Request):

    return templates.TemplateResponse(
        "admin/bot-settings.html",
        {"request": request}
    )        