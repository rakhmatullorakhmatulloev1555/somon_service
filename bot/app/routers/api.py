from fastapi import APIRouter

router = APIRouter(prefix="/api")

tickets = [
    {"id":1,"title":"iPhone repair","status":"new"},
    {"id":2,"title":"Laptop repair","status":"repair"},
]

@router.get("/tickets")
async def get_tickets():
    return tickets
