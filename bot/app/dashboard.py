from fastapi import Request
from fastapi.responses import RedirectResponse

@router.get("/admin")
async def admin_page(request: Request):

    if "user" not in request.session:
        return RedirectResponse("/login")

    return templates.TemplateResponse(
        "admin.html",
        {"request": request}
    )
