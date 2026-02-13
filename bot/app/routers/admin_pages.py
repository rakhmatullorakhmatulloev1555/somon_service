from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

@router.get("/admin")
def dashboard(request: Request):
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request}
    )

@router.get("/admin/orders")
def orders(request: Request):
    return templates.TemplateResponse(
        "admin/orders.html",
        {"request": request}
    )

@router.get("/admin/calendar")
def calendar(request: Request):
    return templates.TemplateResponse(
        "admin/calendar.html",
        {"request": request}
    )
