# app/migrations.py
"""
Скрипт для миграции базы данных
Запуск: python -m app.migrations
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal
from app.models.part import Part, PartCategory, PartSupplier
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    """Выполнение миграций"""
    db = SessionLocal()
    try:
        logger.info("🔄 Запуск миграций...")
        
        # ============================================
        # МИГРАЦИЯ 1: Создание базовых категорий
        # ============================================
        logger.info("Миграция 1: Создание базовых категорий...")
        
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
        
        created_count = 0
        for cat_data in categories:
            existing = db.query(PartCategory).filter(
                PartCategory.name == cat_data["name"]
            ).first()
            
            if not existing:
                category = PartCategory(
                    name=cat_data["name"],
                    icon=cat_data["icon"],
                    description=cat_data["description"],
                    created_at=datetime.utcnow()
                )
                db.add(category)
                created_count += 1
        
        if created_count > 0:
            db.commit()
            logger.info(f"✅ Создано {created_count} категорий")
        else:
            logger.info("✅ Категории уже существуют")
        
        # ============================================
        # МИГРАЦИЯ 2: Создание базовых поставщиков
        # ============================================
        logger.info("Миграция 2: Создание базовых поставщиков...")
        
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
        
        created_suppliers = 0
        for sup_data in suppliers:
            existing = db.query(PartSupplier).filter(
                PartSupplier.name == sup_data["name"]
            ).first()
            
            if not existing:
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
                created_suppliers += 1
        
        if created_suppliers > 0:
            db.commit()
            logger.info(f"✅ Создано {created_suppliers} поставщиков")
        else:
            logger.info("✅ Поставщики уже существуют")
        
        # ============================================
        # МИГРАЦИЯ 3: Обновление существующих запчастей
        # ============================================
        logger.info("Миграция 3: Обновление структуры запчастей...")
        
        # Здесь можно добавить обновления для существующих данных
        
        logger.info("🎉 Все миграции успешно выполнены!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении миграций: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_backup():
    """Создание бэкапа базы данных"""
    import shutil
    from datetime import datetime
    
    try:
        db_path = "service_bot.db"  # Путь к вашей БД
        backup_path = f"backups/service_bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        os.makedirs("backups", exist_ok=True)
        
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)
            logger.info(f"✅ Бэкап создан: {backup_path}")
        else:
            logger.warning("⚠️ Файл базы данных не найден")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при создании бэкапа: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Миграции базы данных")
    parser.add_argument("--backup", action="store_true", help="Создать бэкап")
    args = parser.parse_args()
    
    if args.backup:
        create_backup()
    else:
        run_migrations()