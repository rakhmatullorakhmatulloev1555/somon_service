# app/init_db.py
"""
Скрипт для инициализации базы данных и создания всех таблиц
Запуск: python -m app.init_db
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base

# Импортируем все модели через __init__.py
from app.models import (
    Client, Master, Ticket, PartCategory, 
    PartSupplier, Part, PartTransaction
)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Создание всех таблиц в базе данных"""
    try:
        logger.info("🚀 Начинаем создание таблиц в базе данных...")
        
        # Создаем все таблицы
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Все таблицы успешно созданы!")
        
        # Выводим список созданных таблиц
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"📋 Список таблиц ({len(tables)}):")
        for table in sorted(tables):
            logger.info(f"   - {table}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при создании таблиц: {e}")
        import traceback
        traceback.print_exc()
        raise

def drop_tables():
    """Удаление всех таблиц (ОСТОРОЖНО!)"""
    try:
        logger.warning("⚠️ ВНИМАНИЕ: Удаление всех таблиц!")
        confirm = input("Вы уверены? (yes/no): ")
        if confirm.lower() == 'yes':
            Base.metadata.drop_all(bind=engine)
            logger.info("✅ Все таблицы удалены")
        else:
            logger.info("❌ Операция отменена")
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении таблиц: {e}")
        raise

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Управление базой данных")
    parser.add_argument("--drop", action="store_true", help="Удалить все таблицы")
    args = parser.parse_args()
    
    if args.drop:
        drop_tables()
    else:
        create_tables()