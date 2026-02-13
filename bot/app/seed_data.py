# app/seed_data.py
"""
Скрипт для добавления тестовых данных
Запуск: python -m app.seed_data
"""
import sys
import os
import random
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal

# ИМПОРТИРУЕМ ВСЕ МОДЕЛИ В ПРАВИЛЬНОМ ПОРЯДКЕ
from app.models.client import Client
from app.models.master import Master
from app.models.ticket import Ticket, DeliveryMethod
from app.models.part import PartCategory, PartSupplier, Part, PartTransaction

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_categories_and_suppliers():
    """Добавление тестовых категорий и поставщиков"""
    db = SessionLocal()
    try:
        logger.info("🌱 Добавление категорий и поставщиков...")
        
        # Проверяем, есть ли уже категории
        existing_categories = db.query(PartCategory).count()
        if existing_categories > 0:
            logger.info(f"✅ В базе уже есть {existing_categories} категорий. Пропускаем...")
        else:
            # Категории
            categories = [
                {"name": "Экраны", "icon": "fas fa-mobile-alt", "description": "Дисплеи и сенсорные стекла"},
                {"name": "Аккумуляторы", "icon": "fas fa-battery-full", "description": "Батареи и аккумуляторы"},
                {"name": "Корпуса", "icon": "fas fa-mobile", "description": "Задние крышки и корпуса"},
                {"name": "Клавиатуры", "icon": "fas fa-keyboard", "description": "Клавиатуры для ноутбуков"},
                {"name": "Материнские платы", "icon": "fas fa-microchip", "description": "Системные платы"},
                {"name": "Разъемы", "icon": "fas fa-plug", "description": "USB, зарядки, аудио"},
                {"name": "Камеры", "icon": "fas fa-camera", "description": "Фронтальные и основные камеры"},
                {"name": "Динамики", "icon": "fas fa-volume-up", "description": "Звуковые динамики"},
                {"name": "Шлейфы", "icon": "fas fa-link", "description": "Соединительные шлейфы"},
                {"name": "Другое", "icon": "fas fa-box", "description": "Прочие запчасти"}
            ]
            
            for cat_data in categories:
                category = PartCategory(
                    name=cat_data["name"],
                    icon=cat_data["icon"],
                    description=cat_data["description"],
                    created_at=datetime.utcnow()
                )
                db.add(category)
            
            db.commit()
            logger.info(f"✅ Добавлено {len(categories)} категорий")
        
        # Проверяем, есть ли уже поставщики
        existing_suppliers = db.query(PartSupplier).count()
        if existing_suppliers > 0:
            logger.info(f"✅ В базе уже есть {existing_suppliers} поставщиков. Пропускаем...")
        else:
            # Поставщики
            suppliers = [
                {
                    "name": "TechParts Ltd.",
                    "contact_person": "Иван Петров",
                    "phone": "+992 900 123 456",
                    "email": "info@techparts.tj",
                    "address": "г. Душанбе, ул. Айни 123"
                },
                {
                    "name": "MobileComponents",
                    "contact_person": "Алишер Каримов",
                    "phone": "+992 901 234 567",
                    "email": "sales@mobilecomponents.tj",
                    "address": "г. Душанбе, пр. Рудаки 45"
                },
                {
                    "name": "ComputerSpare",
                    "contact_person": "Дмитрий Соколов",
                    "phone": "+992 902 345 678",
                    "email": "order@computerspare.tj",
                    "address": "г. Душанбе, ул. Борбад 78"
                }
            ]
            
            for sup_data in suppliers:
                supplier = PartSupplier(
                    name=sup_data["name"],
                    contact_person=sup_data["contact_person"],
                    phone=sup_data["phone"],
                    email=sup_data["email"],
                    address=sup_data["address"],
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.add(supplier)
            
            db.commit()
            logger.info(f"✅ Добавлено {len(suppliers)} поставщиков")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка при добавлении категорий: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def seed_parts():
    """Добавление тестовых запчастей"""
    db = SessionLocal()
    try:
        logger.info("🌱 Добавление тестовых запчастей...")
        
        # Проверяем, есть ли уже запчасти
        existing_parts = db.query(Part).count()
        if existing_parts > 0:
            logger.info(f"✅ В базе уже есть {existing_parts} запчастей. Пропускаем...")
            return
        
        # Получаем категории
        categories = db.query(PartCategory).all()
        if not categories:
            logger.warning("⚠️ Категории не найдены. Сначала добавьте категории.")
            return
        
        categories_dict = {c.name: c.id for c in categories}
        
        # Получаем поставщиков
        suppliers = db.query(PartSupplier).all()
        suppliers_ids = [s.id for s in suppliers] if suppliers else [None]
        
        # Тестовые данные запчастей
        parts_data = [
            # Экраны
            {"name": "Экран iPhone 12", "sku": "IP12-SCR-001", "brand": "Apple", 
             "category": "Экраны", "purchase_price": 180, "sale_price": 350, 
             "stock": 8, "min_stock": 5},
            {"name": "Экран iPhone 11", "sku": "IP11-SCR-002", "brand": "Apple", 
             "category": "Экраны", "purchase_price": 150, "sale_price": 300, 
             "stock": 12, "min_stock": 5},
            {"name": "Экран Samsung A52", "sku": "SA52-SCR-003", "brand": "Samsung", 
             "category": "Экраны", "purchase_price": 160, "sale_price": 280, 
             "stock": 6, "min_stock": 5},
            {"name": "Экран Xiaomi Redmi Note 10", "sku": "RN10-SCR-004", "brand": "Xiaomi", 
             "category": "Экраны", "purchase_price": 140, "sale_price": 250, 
             "stock": 4, "min_stock": 5},
            
            # Аккумуляторы
            {"name": "Аккумулятор iPhone XR", "sku": "IPXR-BAT-001", "brand": "Apple", 
             "category": "Аккумуляторы", "purchase_price": 120, "sale_price": 180, 
             "stock": 15, "min_stock": 10},
            {"name": "Аккумулятор Samsung S21", "sku": "S21-BAT-002", "brand": "Samsung", 
             "category": "Аккумуляторы", "purchase_price": 110, "sale_price": 170, 
             "stock": 8, "min_stock": 8},
            {"name": "Аккумулятор Xiaomi", "sku": "XIAOMI-BAT-003", "brand": "Xiaomi", 
             "category": "Аккумуляторы", "purchase_price": 90, "sale_price": 150, 
             "stock": 20, "min_stock": 10},
            
            # Корпуса
            {"name": "Корпус Samsung S21", "sku": "S21-CAS-001", "brand": "Samsung", 
             "category": "Корпуса", "purchase_price": 250, "sale_price": 400, 
             "stock": 0, "min_stock": 3},
            {"name": "Корпус iPhone 12", "sku": "IP12-CAS-002", "brand": "Apple", 
             "category": "Корпуса", "purchase_price": 280, "sale_price": 450, 
             "stock": 2, "min_stock": 3},
            
            # Клавиатуры
            {"name": "Клавиатура Lenovo IdeaPad", "sku": "LEN-KBD-001", "brand": "Lenovo", 
             "category": "Клавиатуры", "purchase_price": 150, "sale_price": 200, 
             "stock": 3, "min_stock": 5},
            {"name": "Клавиатура HP Pavilion", "sku": "HP-KBD-002", "brand": "HP", 
             "category": "Клавиатуры", "purchase_price": 140, "sale_price": 190, 
             "stock": 5, "min_stock": 5},
            
            # Материнские платы
            {"name": "Материнская плата ASUS", "sku": "ASUS-MB-001", "brand": "ASUS", 
             "category": "Материнские платы", "purchase_price": 1200, "sale_price": 1800, 
             "stock": 2, "min_stock": 2},
            {"name": "Материнская плата MSI", "sku": "MSI-MB-002", "brand": "MSI", 
             "category": "Материнские платы", "purchase_price": 1100, "sale_price": 1700, 
             "stock": 1, "min_stock": 2},
            
            # Разъемы
            {"name": "Разъем зарядки iPhone", "sku": "IP-CHG-001", "brand": "Apple", 
             "category": "Разъемы", "purchase_price": 30, "sale_price": 60, 
             "stock": 25, "min_stock": 10},
            {"name": "Разъем USB Type-C", "sku": "USB-C-002", "brand": "Universal", 
             "category": "Разъемы", "purchase_price": 20, "sale_price": 40, 
             "stock": 30, "min_stock": 15},
            
            # Динамики
            {"name": "Динамик iPhone 12", "sku": "IP12-SPK-001", "brand": "Apple", 
             "category": "Динамики", "purchase_price": 45, "sale_price": 80, 
             "stock": 7, "min_stock": 5},
            {"name": "Динамик Samsung", "sku": "S21-SPK-002", "brand": "Samsung", 
             "category": "Динамики", "purchase_price": 40, "sale_price": 75, 
             "stock": 5, "min_stock": 5},
        ]
        
        created_count = 0
        for part_data in parts_data:
            # Проверяем, существует ли уже такая запчасть
            existing = db.query(Part).filter(Part.sku == part_data["sku"]).first()
            
            if not existing:
                category_id = categories_dict.get(part_data["category"])
                supplier_id = random.choice(suppliers_ids) if suppliers_ids else None
                
                part = Part(
                    name=part_data["name"],
                    sku=part_data["sku"],
                    brand=part_data["brand"],
                    category_id=category_id,
                    purchase_price=part_data["purchase_price"],
                    sale_price=part_data["sale_price"],
                    stock=part_data["stock"],
                    min_stock=part_data["min_stock"],
                    supplier_id=supplier_id,
                    description=f"{part_data['name']} - оригинальная запчасть",
                    notes="Тестовые данные",
                    is_active=True,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                )
                db.add(part)
                db.flush()  # Получаем ID
                
                # Создаем транзакцию прихода
                if part.stock > 0:
                    transaction = PartTransaction(
                        part_id=part.id,
                        transaction_type="in",
                        quantity=part.stock,
                        price=part.purchase_price,
                        notes="Начальный остаток",
                        created_at=part.created_at
                    )
                    db.add(transaction)
                
                created_count += 1
        
        if created_count > 0:
            db.commit()
            logger.info(f"✅ Добавлено {created_count} тестовых запчастей")
        else:
            logger.info("✅ Тестовые запчасти уже существуют")
        
        # Статистика
        total_parts = db.query(Part).count()
        total_categories = db.query(PartCategory).count()
        total_suppliers = db.query(PartSupplier).count()
        low_stock = db.query(Part).filter(
            Part.is_active == True,
            Part.stock < Part.min_stock
        ).count()
        
        logger.info(f"📊 Статистика склада:")
        logger.info(f"   - Всего запчастей: {total_parts}")
        logger.info(f"   - Категорий: {total_categories}")
        logger.info(f"   - Поставщиков: {total_suppliers}")
        logger.info(f"   - Низкий запас: {low_stock}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка при добавлении тестовых данных: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

def clear_all():
    """Очистка всех тестовых данных"""
    db = SessionLocal()
    try:
        logger.warning("⚠️ Очистка всех тестовых данных...")
        confirm = input("Удалить все данные из таблиц? (yes/no): ")
        
        if confirm.lower() == 'yes':
            # Удаляем в правильном порядке (с учетом внешних ключей)
            db.query(PartTransaction).delete()
            db.query(Part).delete()
            db.query(PartSupplier).delete()
            db.query(PartCategory).delete()
            db.query(Ticket).delete()
            db.query(Master).delete()
            db.query(Client).delete()
            
            db.commit()
            logger.info("✅ Все данные удалены")
        else:
            logger.info("❌ Операция отменена")
            
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка при очистке: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def seed_all():
    """Добавить все тестовые данные"""
    logger.info("=" * 50)
    logger.info("🌱 НАЧАЛО ДОБАВЛЕНИЯ ТЕСТОВЫХ ДАННЫХ")
    logger.info("=" * 50)
    
    seed_categories_and_suppliers()
    seed_parts()
    
    logger.info("=" * 50)
    logger.info("✅ ТЕСТОВЫЕ ДАННЫЕ УСПЕШНО ДОБАВЛЕНЫ")
    logger.info("=" * 50)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Добавление тестовых данных")
    parser.add_argument("--clear", action="store_true", help="Очистить все тестовые данные")
    parser.add_argument("--categories", action="store_true", help="Только категории и поставщики")
    parser.add_argument("--parts", action="store_true", help="Только запчасти")
    args = parser.parse_args()
    
    if args.clear:
        clear_all()
    elif args.categories:
        seed_categories_and_suppliers()
    elif args.parts:
        seed_parts()
    else:
        seed_all()