# app/routers/masters.py
from fastapi import APIRouter, HTTPException
from app.database import SessionLocal
from app.models.master import Master
from app.services.master_service import create_master, get_all_masters, update_master, delete_master
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/masters", tags=["masters"])

class MasterCreate(BaseModel):
    name: str
    surname: str
    phone: Optional[str] = None
    specialization: Optional[str] = None
    experience: Optional[int] = 0
    skills: Optional[str] = None  # Добавляем поле skills
    status: Optional[str] = "active"
    rating: Optional[float] = 0
    schedule: Optional[str] = None
    salary: Optional[int] = 0
    notes: Optional[str] = None

class MasterUpdate(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    phone: Optional[str] = None
    specialization: Optional[str] = None
    experience: Optional[int] = None
    skills: Optional[str] = None  # Добавляем поле skills
    status: Optional[str] = None
    rating: Optional[float] = None
    schedule: Optional[str] = None
    salary: Optional[int] = None
    notes: Optional[str] = None

@router.get("")
async def get_masters():
    """Получить всех мастеров"""
    db = SessionLocal()
    try:
        masters = db.query(Master).all()
        result = []
        for m in masters:
            result.append({
                "id": m.id,
                "name": m.name,
                "surname": m.surname or "",
                "full_name": f"{m.name} {m.surname or ''}".strip(),
                "phone": m.phone or "",
                "specialization": m.specialization or "",
                "experience": m.experience or 0,
                "skills": m.skills or "",  # Отправляем как строку
                "status": m.status or "active",
                "rating": m.rating or 0,
                "rating_count": m.rating_count or 0,
                "active_orders": m.active_orders or 0,
                "completed_orders": m.completed_orders or 0,
                "schedule": m.notes,  # Временно используем notes для schedule
                "salary": 0,  # Заглушка
                "notes": m.notes or "",
                "telegram_id": m.telegram_id,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "updated_at": m.updated_at.isoformat() if m.updated_at else None
            })
        return result
    finally:
        db.close()

@router.post("")
async def create_master_endpoint(master: MasterCreate):
    """Создать нового мастера"""
    db = SessionLocal()
    try:
        master_data = master.dict(exclude_unset=True)
        new_master = create_master(db, master_data)
        db.commit()
        return {"success": True, "message": "Мастер создан", "id": new_master.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@router.put("/{master_id}")
async def update_master_endpoint(master_id: int, master: MasterUpdate):
    """Обновить мастера"""
    db = SessionLocal()
    try:
        master_data = master.dict(exclude_unset=True)
        updated_master = update_master(db, master_id, master_data)
        if not updated_master:
            raise HTTPException(status_code=404, detail="Мастер не найден")
        db.commit()
        return {"success": True, "message": "Мастер обновлен"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@router.delete("/{master_id}")
async def delete_master_endpoint(master_id: int):
    """Удалить мастера"""
    db = SessionLocal()
    try:
        success = delete_master(db, master_id)
        if not success:
            raise HTTPException(status_code=404, detail="Мастер не найден")
        db.commit()
        return {"success": True, "message": "Мастер удален"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()