# app/services/part_service.py
from app.database import SessionLocal
from app.models.part import Part, PartCategory, PartSupplier, PartTransaction
from sqlalchemy.orm import joinedload
from sqlalchemy import func, or_
import logging

logger = logging.getLogger(__name__)

# ========================
# CATEGORY CRUD
# ========================

def get_all_categories():
    """Получить все категории"""
    db = SessionLocal()
    try:
        categories = db.query(PartCategory).all()
        result = []
        for cat in categories:
            # Подсчитываем количество запчастей в категории
            parts_count = db.query(Part).filter(Part.category_id == cat.id).count()
            result.append({
                "id": cat.id,
                "name": cat.name,
                "description": cat.description,
                "icon": cat.icon,
                "count": parts_count,
                "created_at": cat.created_at.isoformat() if cat.created_at else None
            })
        return result
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return []
    finally:
        db.close()

def create_category(data):
    """Создать категорию"""
    db = SessionLocal()
    try:
        category = PartCategory(
            name=data.get("name"),
            description=data.get("description"),
            icon=data.get("icon", "fas fa-box")
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating category: {e}")
        raise
    finally:
        db.close()

def update_category(category_id, data):
    """Обновить категорию"""
    db = SessionLocal()
    try:
        category = db.query(PartCategory).filter(PartCategory.id == category_id).first()
        if not category:
            return None
        
        if "name" in data:
            category.name = data["name"]
        if "description" in data:
            category.description = data["description"]
        if "icon" in data:
            category.icon = data["icon"]
        
        db.commit()
        db.refresh(category)
        return category
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating category: {e}")
        raise
    finally:
        db.close()

def delete_category(category_id):
    """Удалить категорию"""
    db = SessionLocal()
    try:
        # Проверяем, есть ли запчасти в этой категории
        parts_count = db.query(Part).filter(Part.category_id == category_id).count()
        if parts_count > 0:
            return False, f"Нельзя удалить категорию: {parts_count} запчастей в этой категории"
        
        category = db.query(PartCategory).filter(PartCategory.id == category_id).first()
        if category:
            db.delete(category)
            db.commit()
            return True, "Категория удалена"
        return False, "Категория не найдена"
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting category: {e}")
        return False, str(e)
    finally:
        db.close()

def delete_supplier(supplier_id):
    """Удалить поставщика"""
    db = SessionLocal()
    try:
        # Проверяем, есть ли запчасти от этого поставщика
        parts_count = db.query(Part).filter(Part.supplier_id == supplier_id).count()
        if parts_count > 0:
            return False, f"Нельзя удалить поставщика: {parts_count} запчастей от этого поставщика"
        
        supplier = db.query(PartSupplier).filter(PartSupplier.id == supplier_id).first()
        if supplier:
            db.delete(supplier)
            db.commit()
            return True, "Поставщик удален"
        return False, "Поставщик не найден"
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting supplier: {e}")
        return False, str(e)
    finally:
        db.close()
# ========================
# PART CRUD
# ========================

def get_all_parts():
    """Получить все запчасти"""
    db = SessionLocal()
    try:
        parts = db.query(Part).options(
            joinedload(Part.category),
            joinedload(Part.supplier)
        ).all()
        
        result = []
        for part in parts:
            result.append({
                "id": part.id,
                "name": part.name,
                "sku": part.sku,
                "brand": part.brand,
                "category_id": part.category_id,
                "category_name": part.category.name if part.category else "Без категории",
                "category_icon": part.category.icon if part.category else "fas fa-box",
                "purchase_price": part.purchase_price,
                "sale_price": part.sale_price,
                "stock": part.stock,
                "min_stock": part.min_stock,
                "status": part.status,
                "supplier_id": part.supplier_id,
                "supplier_name": part.supplier.name if part.supplier else None,
                "description": part.description,
                "notes": part.notes,
                "image_url": part.image_url,
                "total_value": part.total_value,
                "is_active": part.is_active,
                "created_at": part.created_at.isoformat() if part.created_at else None
            })
        return result
    except Exception as e:
        logger.error(f"Error getting parts: {e}")
        return []
    finally:
        db.close()

def get_part(part_id):
    """Получить запчасть по ID"""
    db = SessionLocal()
    try:
        part = db.query(Part).options(
            joinedload(Part.category),
            joinedload(Part.supplier)
        ).filter(Part.id == part_id).first()
        
        if not part:
            return None
        
        # Собираем данные в словарь ПОКА СЕССИЯ ОТКРЫТА
        result = {
            "id": part.id,
            "name": part.name,
            "sku": part.sku,
            "brand": part.brand,
            "category_id": part.category_id,
            "category_name": part.category.name if part.category else "Без категории",
            "purchase_price": part.purchase_price,
            "sale_price": part.sale_price,
            "stock": part.stock,
            "min_stock": part.min_stock,
            "status": part.status,
            "supplier_id": part.supplier_id,
            "supplier_name": part.supplier.name if part.supplier else None,
            "description": part.description,
            "notes": part.notes,
            "image_url": part.image_url,
            "location": part.location,
            "is_active": part.is_active
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting part {part_id}: {e}")
        return None
    finally:
        db.close()

def create_part(data):
    """Создать запчасть"""
    db = SessionLocal()
    try:
        # Проверяем уникальность SKU
        existing = db.query(Part).filter(Part.sku == data.get("sku")).first()
        if existing:
            raise ValueError(f"Запчасть с артикулом {data.get('sku')} уже существует")
        
        part = Part(
            name=data.get("name"),
            sku=data.get("sku"),
            brand=data.get("brand"),
            category_id=data.get("category_id"),
            purchase_price=data.get("purchase_price", 0),
            sale_price=data.get("sale_price", 0),
            stock=data.get("stock", 0),
            min_stock=data.get("min_stock", 5),
            supplier_id=data.get("supplier_id"),
            description=data.get("description"),
            notes=data.get("notes"),
            image_url=data.get("image_url"),
            location=data.get("location"),
            is_active=data.get("is_active", True)
        )
        db.add(part)
        db.flush()  # Получаем ID без коммита
        
        # Создаем транзакцию прихода
        if part.stock > 0:
            transaction = PartTransaction(
                part_id=part.id,
                transaction_type="in",
                quantity=part.stock,
                price=part.purchase_price,
                notes="Начальный остаток"
            )
            db.add(transaction)
        
        db.commit()
        
        # Обновляем объект после коммита
        db.refresh(part)
        
        # Возвращаем объект, который все еще привязан к сессии
        return part
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating part: {e}")
        raise
    finally:
        db.close()  # Закрываем сессию ПОСЛЕ того как получили все данные

def update_part(part_id, data):
    """Обновить запчасть"""
    db = SessionLocal()
    try:
        part = db.query(Part).filter(Part.id == part_id).first()
        if not part:
            return None
        
        old_stock = part.stock
        
        if "name" in data:
            part.name = data["name"]
        if "sku" in data:
            # Проверяем уникальность SKU
            existing = db.query(Part).filter(
                Part.sku == data["sku"],
                Part.id != part_id
            ).first()
            if existing:
                raise ValueError(f"Запчасть с артикулом {data['sku']} уже существует")
            part.sku = data["sku"]
        if "brand" in data:
            part.brand = data["brand"]
        if "category_id" in data:
            part.category_id = data["category_id"]
        if "purchase_price" in data:
            part.purchase_price = data["purchase_price"]
        if "sale_price" in data:
            part.sale_price = data["sale_price"]
        if "stock" in data:
            part.stock = data["stock"]
        if "min_stock" in data:
            part.min_stock = data["min_stock"]
        if "supplier_id" in data:
            part.supplier_id = data["supplier_id"]
        if "description" in data:
            part.description = data["description"]
        if "notes" in data:
            part.notes = data["notes"]
        if "image_url" in data:
            part.image_url = data["image_url"]
        if "location" in data:
            part.location = data["location"]
        if "is_active" in data:
            part.is_active = data["is_active"]
        
        db.commit()
        
        # Если количество изменилось, создаем транзакцию
        if "stock" in data and data["stock"] != old_stock:
            diff = data["stock"] - old_stock
            transaction = PartTransaction(
                part_id=part.id,
                transaction_type="in" if diff > 0 else "out",
                quantity=abs(diff),
                price=part.purchase_price,
                notes="Корректировка запаса"
            )
            db.add(transaction)
            db.commit()
        
        db.refresh(part)
        return part
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating part {part_id}: {e}")
        raise
    finally:
        db.close()

def delete_part(part_id):
    """Удалить запчасть"""
    db = SessionLocal()
    try:
        part = db.query(Part).filter(Part.id == part_id).first()
        if part:
            # Удаляем связанные транзакции
            db.query(PartTransaction).filter(PartTransaction.part_id == part_id).delete()
            db.delete(part)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting part {part_id}: {e}")
        return False
    finally:
        db.close()

def adjust_stock(part_id, quantity, transaction_type="in", notes=""):
    """Изменить количество запчасти на складе"""
    db = SessionLocal()
    try:
        part = db.query(Part).filter(Part.id == part_id).first()
        if not part:
            return False, "Запчасть не найдена"
        
        if transaction_type == "out" and part.stock < quantity:
            return False, f"Недостаточно запчастей на складе (есть: {part.stock}, нужно: {quantity})"
        
        # Изменяем количество
        if transaction_type == "in":
            part.stock += quantity
        elif transaction_type == "out":
            part.stock -= quantity
        elif transaction_type == "return":
            part.stock += quantity
        
        # Создаем транзакцию
        transaction = PartTransaction(
            part_id=part.id,
            transaction_type=transaction_type,
            quantity=quantity,
            price=part.purchase_price,
            notes=notes
        )
        db.add(transaction)
        db.commit()
        
        return True, f"Запас обновлен. Новый остаток: {part.stock}"
    except Exception as e:
        db.rollback()
        logger.error(f"Error adjusting stock for part {part_id}: {e}")
        return False, str(e)
    finally:
        db.close()

def get_low_stock_parts():
    """Получить запчасти с низким запасом"""
    db = SessionLocal()
    try:
        parts = db.query(Part).filter(
            Part.is_active == True,
            Part.stock < Part.min_stock
        ).all()
        
        result = []
        for part in parts:
            result.append({
                "id": part.id,
                "name": part.name,
                "sku": part.sku,
                "stock": part.stock,
                "min_stock": part.min_stock,
                "category_name": part.category.name if part.category else "Без категории"
            })
        return result
    except Exception as e:
        logger.error(f"Error getting low stock parts: {e}")
        return []
    finally:
        db.close()

# ========================
# SUPPLIER CRUD
# ========================

def get_all_suppliers():
    """Получить всех поставщиков"""
    db = SessionLocal()
    try:
        suppliers = db.query(PartSupplier).all()
        result = []
        for supplier in suppliers:
            parts_count = db.query(Part).filter(Part.supplier_id == supplier.id).count()
            result.append({
                "id": supplier.id,
                "name": supplier.name,
                "contact_person": supplier.contact_person,
                "phone": supplier.phone,
                "email": supplier.email,
                "address": supplier.address,
                "notes": supplier.notes,
                "is_active": supplier.is_active,
                "parts_count": parts_count
            })
        return result
    except Exception as e:
        logger.error(f"Error getting suppliers: {e}")
        return []
    finally:
        db.close()

def create_supplier(data):
    """Создать поставщика"""
    db = SessionLocal()
    try:
        supplier = PartSupplier(
            name=data.get("name"),
            contact_person=data.get("contact_person"),
            phone=data.get("phone"),
            email=data.get("email"),
            address=data.get("address"),
            notes=data.get("notes")
        )
        db.add(supplier)
        db.commit()
        db.refresh(supplier)
        return supplier
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating supplier: {e}")
        raise
    finally:
        db.close()

# ========================
# STATISTICS
# ========================

def get_part_statistics():
    """Получить статистику по запчастям"""
    db = SessionLocal()
    try:
        total_parts = db.query(Part).count()
        total_categories = db.query(PartCategory).count()
        total_suppliers = db.query(PartSupplier).count()
        low_stock = db.query(Part).filter(
            Part.is_active == True,
            Part.stock < Part.min_stock
        ).count()
        
        total_value = db.query(func.sum(Part.purchase_price * Part.stock)).scalar() or 0
        
        return {
            "total_parts": total_parts,
            "total_categories": total_categories,
            "total_suppliers": total_suppliers,
            "low_stock": low_stock,
            "total_value": float(total_value)
        }
    except Exception as e:
        logger.error(f"Error getting part statistics: {e}")
        return {
            "total_parts": 0,
            "total_categories": 0,
            "total_suppliers": 0,
            "low_stock": 0,
            "total_value": 0
        }
    finally:
        db.close()