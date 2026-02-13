from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.client import Client

router = APIRouter(prefix="/api/clients", tags=["Clients"])


@router.get("/")
def get_clients(db: Session = Depends(get_db)):
    clients = db.query(Client).all()
    return clients