# app/api/routes.py
# app/api/routes.py
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from app.api.admin_api import router as admin_api_router
from app.api.statistics_api import router as statistics_api_router
from app.api.events_api import router as events_api_router

router = APIRouter()

# Включаем API роутеры
router.include_router(admin_api_router)
router.include_router(events_api_router)
router.include_router(statistics_api_router)

templates = Jinja2Templates(directory="app/templates")

# Зависимость для проверки аутентификации
def require_auth(request: Request):
    """Проверка авторизации пользователя"""
    if not request.session.get("user"):
        raise HTTPException(status_code=302, headers={"Location": "/login"})
    return request.session.get("user")

# Корневой маршрут админки
@router.get("/admin")
async def admin_panel(request: Request, user: str = Depends(require_auth)):
    """Главная страница админки"""
    role = request.session.get("role", "user")
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "user": user,
            "role": role
        }
    )

# Все остальные защищенные страницы
@router.get("/admin/orders", response_class=HTMLResponse)
async def orders_page(request: Request, user: str = Depends(require_auth)):
    role = request.session.get("role", "user")
    return templates.TemplateResponse(
        "admin/orders.html",
        {
            "request": request,
            "user": user,
            "role": role
        }
    )

@router.get("/admin/calendar", response_class=HTMLResponse)
async def calendar_page(request: Request, user: str = Depends(require_auth)):
    role = request.session.get("role", "user")
    return templates.TemplateResponse(
        "admin/calendar.html",
        {
            "request": request,
            "user": user,
            "role": role
        }
    )

@router.get("/admin/clients", response_class=HTMLResponse)
async def clients_page(request: Request, user: str = Depends(require_auth)):
    role = request.session.get("role", "user")
    return templates.TemplateResponse(
        "admin/clients.html",
        {
            "request": request,
            "user": user,
            "role": role
        }
    )

@router.get("/admin/masters", response_class=HTMLResponse)
async def masters_page(request: Request, user: str = Depends(require_auth)):
    role = request.session.get("role", "user")
    return templates.TemplateResponse(
        "admin/masters.html",
        {
            "request": request,
            "user": user,
            "role": role
        }
    )

@router.get("/admin/parts", response_class=HTMLResponse)
async def parts_page(request: Request, user: str = Depends(require_auth)):
    role = request.session.get("role", "user")
    return templates.TemplateResponse(
        "admin/parts.html",
        {
            "request": request,
            "user": user,
            "role": role
        }
    )

@router.get("/admin/reports", response_class=HTMLResponse)
async def reports_page(request: Request, user: str = Depends(require_auth)):
    role = request.session.get("role", "user")
    return templates.TemplateResponse(
        "admin/reports.html",
        {
            "request": request,
            "user": user,
            "role": role
        }
    )

@router.get("/admin/finances", response_class=HTMLResponse)
async def finances_page(request: Request, user: str = Depends(require_auth)):
    role = request.session.get("role", "user")
    return templates.TemplateResponse(
        "admin/finances.html",
        {
            "request": request,
            "user": user,
            "role": role
        }
    )

@router.get("/admin/statistics", response_class=HTMLResponse)
async def statistics_page(request: Request, user: str = Depends(require_auth)):
    role = request.session.get("role", "user")
    return templates.TemplateResponse(
        "admin/statistics.html",
        {
            "request": request,
            "user": user,
            "role": role
        }
    )

@router.get("/admin/botsettings", response_class=HTMLResponse)
async def botsettings_page(request: Request, user: str = Depends(require_auth)):
    role = request.session.get("role", "user")
    return templates.TemplateResponse(
        "admin/bot-settings.html",
        {
            "request": request,
            "user": user,
            "role": role
        }
    )

@router.get("/admin/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request, user: str = Depends(require_auth)):
    role = request.session.get("role", "user")
    return templates.TemplateResponse(
        "admin/analytics.html",
        {
            "request": request,
            "user": user,
            "role": role
        }
    )

@router.get("/admin/permissions", response_class=HTMLResponse)
async def permissions_page(request: Request, user: str = Depends(require_auth)):
    role = request.session.get("role", "user")
    return templates.TemplateResponse(
        "admin/permissions.html",
        {
            "request": request,
            "user": user,
            "role": role
        }
    )

@router.get("/admin/ticket/{ticket_id}", response_class=HTMLResponse)
async def ticket_detail_page(request: Request, ticket_id: int, user: str = Depends(require_auth)):
    role = request.session.get("role", "user")
    return templates.TemplateResponse(
        "admin/ticket.html",
        {
            "request": request,
            "ticket_id": ticket_id,
            "user": user,
            "role": role
        }
    )
@router.get("/admin/parts", response_class=HTMLResponse)
async def parts_page(request: Request, user: str = Depends(require_auth)):
    return templates.TemplateResponse(
        "admin/parts.html",
        {"request": request, "user": user}
    )

@router.get("/admin/categories", response_class=HTMLResponse)
async def categories_page(request: Request, user: str = Depends(require_auth)):
    return templates.TemplateResponse(
        "admin/categories.html",
        {"request": request, "user": user}
    )

@router.get("/admin/suppliers", response_class=HTMLResponse)
async def suppliers_page(request: Request, user: str = Depends(require_auth)):
    return templates.TemplateResponse(
        "admin/suppliers.html",
        {"request": request, "user": user}
    )
@router.get("/admin/statistics", response_class=HTMLResponse)
async def statistics_page(request: Request, user: str = Depends(require_auth)):
    """Страница статистики"""
    return templates.TemplateResponse(
        "admin/statistics.html",
        {"request": request, "user": user}
    )        