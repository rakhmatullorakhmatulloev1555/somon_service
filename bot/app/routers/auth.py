from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

users = {
    "admin@servicecenter.ru": {
        "password": "password123",
        "role": "admin"
    },
    "manager@servicecenter.ru": {
        "password": "password123",
        "role": "manager"
    }
}

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):

    user = users.get(username)

    if not user or user["password"] != password:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверный логин или пароль"}
        )

    request.session["user"] = username

    return RedirectResponse("/admin", status_code=302)
