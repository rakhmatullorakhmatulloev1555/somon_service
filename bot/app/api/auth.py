# app/api/auth.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Простые учетные данные
ADMIN_USERS = {
    "admin": "admin123",
    "manager": "manager123"
}

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа"""
    # Если уже авторизован, перенаправляем в админку
    if request.session.get("user"):
        return RedirectResponse(url="/admin")
    
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request}
    )

@router.post("/login")
async def login_post(request: Request):
    """Обработка входа"""
    try:
        form_data = await request.form()
        username = form_data.get("username")
        password = form_data.get("password")
        
        # Проверяем демо-логины из формы
        demo_users = {
            "admin@servicecenter.ru": "password123",
            "manager@servicecenter.ru": "password123",
            "master@servicecenter.ru": "password123",
            "admin": "admin123",
            "manager": "manager123"
        }
        
        if username in demo_users and demo_users[username] == password:
            # Определяем роль
            role = "admin"
            if "manager" in username.lower():
                role = "manager"
            elif "master" in username.lower():
                role = "master"
            
            # Сохраняем в сессии
            request.session["user"] = username
            request.session["role"] = role
            
            # Перенаправляем в админку
            return RedirectResponse(url="/admin", status_code=303)
        else:
            # Возвращаем с ошибкой
            return templates.TemplateResponse(
                "auth/login.html",
                {
                    "request": request,
                    "error": "Неверное имя пользователя или пароль"
                }
            )
    except Exception as e:
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "error": f"Ошибка входа: {str(e)}"
            }
        )

@router.get("/logout")
async def logout(request: Request):
    """Выход из системы"""
    request.session.clear()
    return RedirectResponse(url="/login")