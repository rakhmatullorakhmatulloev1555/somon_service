# app/api/parts_api.py
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from app.services import part_service

router = APIRouter(prefix="/api/parts")

# ========================
# Pydantic Models
# ========================

class PartCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = "fas fa-box"

class PartCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None

class PartCreate(BaseModel):
    name: str
    sku: str
    brand: Optional[str] = None
    category_id: int
    purchase_price: float = 0
    sale_price: float = 0
    stock: int = 0
    min_stock: int = 5
    supplier_id: Optional[int] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    image_url: Optional[str] = None
    location: Optional[str] = None

class PartUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    brand: Optional[str] = None
    category_id: Optional[int] = None
    purchase_price: Optional[float] = None
    sale_price: Optional[float] = None
    stock: Optional[int] = None
    min_stock: Optional[int] = None
    supplier_id: Optional[int] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    image_url: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None

class StockAdjustment(BaseModel):
    quantity: int
    transaction_type: str  # in, out, return
    notes: Optional[str] = None

class SupplierCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

# ========================
# Category Endpoints
# ========================

@router.get("/categories")
async def get_categories():
    """Получить все категории"""
    categories = part_service.get_all_categories()
    return {"success": True, "data": categories}

@router.post("/categories")
async def create_category(data: PartCategoryCreate):
    """Создать категорию"""
    try:
        category = part_service.create_category(data.dict())
        return {"success": True, "data": {"id": category.id, "name": category.name}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/categories/{category_id}")
async def update_category(category_id: int, data: PartCategoryUpdate):
    """Обновить категорию"""
    category = part_service.update_category(category_id, data.dict(exclude_unset=True))
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    return {"success": True, "data": {"id": category.id, "name": category.name}}

@router.delete("/categories/{category_id}")
async def delete_category(category_id: int):
    """Удалить категорию"""
    success, message = part_service.delete_category(category_id)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}

# ========================
# Part Endpoints
# ========================

@router.get("")
async def get_parts():
    """Получить все запчасти"""
    parts = part_service.get_all_parts()
    return {"success": True, "data": parts}

@router.get("/{part_id}")
async def get_part(part_id: int):
    """Получить запчасть по ID"""
    part = part_service.get_part(part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Запчасть не найдена")
    return {"success": True, "data": part}

@router.post("")
async def create_part(data: PartCreate):
    """Создать запчасть"""
    try:
        part = part_service.create_part(data.dict())
        return {"success": True, "data": {"id": part.id, "name": part.name, "sku": part.sku}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{part_id}")
async def update_part(part_id: int, data: PartUpdate):
    """Обновить запчасть"""
    try:
        part = part_service.update_part(part_id, data.dict(exclude_unset=True))
        if not part:
            raise HTTPException(status_code=404, detail="Запчасть не найдена")
        return {"success": True, "data": {"id": part.id, "name": part.name}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{part_id}")
async def delete_part(part_id: int):
    """Удалить запчасть"""
    success = part_service.delete_part(part_id)
    if not success:
        raise HTTPException(status_code=404, detail="Запчасть не найдена")
    return {"success": True, "message": "Запчасть удалена"}

@router.post("/{part_id}/stock")
async def adjust_stock(part_id: int, data: StockAdjustment):
    """Изменить количество на складе"""
    success, message = part_service.adjust_stock(
        part_id, 
        data.quantity, 
        data.transaction_type,
        data.notes
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}

@router.get("/low-stock/all")
async def get_low_stock():
    """Получить запчасти с низким запасом"""
    parts = part_service.get_low_stock_parts()
    return {"success": True, "data": parts}

# ========================
# Supplier Endpoints
# ========================

@router.get("/suppliers/all")
async def get_suppliers():
    """Получить всех поставщиков"""
    suppliers = part_service.get_all_suppliers()
    return {"success": True, "data": suppliers}

@router.post("/suppliers")
async def create_supplier(data: SupplierCreate):
    """Создать поставщика"""
    try:
        supplier = part_service.create_supplier(data.dict())
        return {"success": True, "data": {"id": supplier.id, "name": supplier.name}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ========================
# Statistics
# ========================

@router.get("/stats/all")
async def get_part_stats():
    """Получить статистику по запчастям"""
    try:
        stats = part_service.get_part_statistics()
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"Error in get_part_stats: {e}")
        return {"success": False, "error": str(e)}