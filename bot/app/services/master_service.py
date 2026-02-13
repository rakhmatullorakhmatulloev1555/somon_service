# app/services/master_service.py
from app.models.master import Master
from app.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

def create_master(db: SessionLocal, master_data: dict):
    """Создание нового мастера"""
    try:
        # Проверяем существование мастера по Telegram ID
        if master_data.get('telegram_id'):
            existing = db.query(Master).filter(
                Master.telegram_id == str(master_data['telegram_id'])
            ).first()
            if existing:
                return existing
        
        # Создаем мастера со всеми полями, включая skills
        master = Master(
            name=master_data.get('name', ''),
            surname=master_data.get('surname', ''),
            phone=master_data.get('phone', ''),
            telegram_id=str(master_data.get('telegram_id')) if master_data.get('telegram_id') else None,
            specialization=master_data.get('specialization', ''),
            experience=master_data.get('experience', 0),
            skills=master_data.get('skills', ''),  # ДОБАВЛЯЕМ ПОЛЕ SKILLS
            rating=master_data.get('rating', 0.0),
            rating_count=master_data.get('rating_count', 0),
            status=master_data.get('status', 'active'),
            completed_orders=master_data.get('completed_orders', 0),
            active_orders=master_data.get('active_orders', 0),
            notes=master_data.get('notes', '')  # ДОБАВЛЯЕМ ПОЛЕ NOTES
        )
        
        db.add(master)
        db.commit()
        db.refresh(master)
        
        logger.info(f"✅ Создан новый мастер: {master.name} {master.surname or ''} (ID: {master.id})")
        logger.info(f"   📋 Навыки: {master.skills or 'не указаны'}")
        return master
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка при создании мастера: {e}")
        raise

def get_all_masters(db: SessionLocal = None):
    """Получение всех мастеров"""
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    
    try:
        masters = db.query(Master).all()
        return masters
    except Exception as e:
        logger.error(f"❌ Ошибка при получении списка мастеров: {e}")
        return []
    finally:
        if close_db:
            db.close()

def get_master_by_telegram_id(db: SessionLocal, telegram_id: str):
    """Получение мастера по Telegram ID"""
    try:
        master = db.query(Master).filter(
            Master.telegram_id == str(telegram_id)
        ).first()
        return master
    except Exception as e:
        logger.error(f"❌ Ошибка при получении мастера по Telegram ID {telegram_id}: {e}")
        return None

def update_master(db: SessionLocal, master_id: int, master_data: dict):
    """Обновление данных мастера"""
    try:
        master = db.query(Master).filter(Master.id == master_id).first()
        if not master:
            return None
        
        # Обновляем существующие поля
        if 'name' in master_data:
            master.name = master_data['name']
        if 'surname' in master_data:
            master.surname = master_data['surname']
        if 'phone' in master_data:
            master.phone = master_data['phone']
        if 'telegram_id' in master_data:
            master.telegram_id = str(master_data['telegram_id'])
        if 'specialization' in master_data:
            master.specialization = master_data['specialization']
        if 'experience' in master_data:
            master.experience = master_data['experience']
        if 'skills' in master_data:  # ДОБАВЛЯЕМ ОБНОВЛЕНИЕ НАВЫКОВ
            master.skills = master_data['skills']
        if 'rating' in master_data:
            master.rating = master_data['rating']
        if 'rating_count' in master_data:
            master.rating_count = master_data['rating_count']
        if 'status' in master_data:
            master.status = master_data['status']
        if 'completed_orders' in master_data:
            master.completed_orders = master_data['completed_orders']
        if 'active_orders' in master_data:
            master.active_orders = master_data['active_orders']
        if 'notes' in master_data:  # ДОБАВЛЯЕМ ОБНОВЛЕНИЕ ЗАМЕТОК
            master.notes = master_data['notes']
        
        db.commit()
        db.refresh(master)
        logger.info(f"✅ Обновлен мастер ID: {master_id}")
        if master.skills:
            logger.info(f"   📋 Навыки: {master.skills}")
        return master
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка при обновлении мастера {master_id}: {e}")
        raise

def delete_master(db: SessionLocal, master_id: int):
    """Удаление мастера"""
    try:
        master = db.query(Master).filter(Master.id == master_id).first()
        if master:
            db.delete(master)
            db.commit()
            logger.info(f"✅ Удален мастер ID: {master_id}")
            return True
        return False
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка при удалении мастера {master_id}: {e}")
        raise

def update_master_rating(db: SessionLocal, master_id: int, new_rating: int):
    """Обновление рейтинга мастера"""
    try:
        master = db.query(Master).filter(Master.id == master_id).first()
        if not master:
            return None
        
        # Рассчитываем новый рейтинг
        if master.rating_count > 0:
            master.rating = (
                (master.rating * master.rating_count + new_rating) 
                / (master.rating_count + 1)
            )
        else:
            master.rating = new_rating
        
        master.rating_count += 1
        db.commit()
        db.refresh(master)
        
        logger.info(f"⭐ Обновлен рейтинг мастера {master_id}: {master.rating:.2f} ({master.rating_count} оценок)")
        return master
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка при обновлении рейтинга мастера {master_id}: {e}")
        raise

def get_master_with_skills(db: SessionLocal, master_id: int):
    """Получение мастера с навыками в виде массива"""
    try:
        master = db.query(Master).filter(Master.id == master_id).first()
        if not master:
            return None
        
        # Преобразуем строку навыков в массив
        skills_list = []
        if master.skills:
            skills_list = [s.strip() for s in master.skills.split(',') if s.strip()]
        
        # Создаем словарь с данными
        master_data = {
            "id": master.id,
            "name": master.name,
            "surname": master.surname,
            "full_name": f"{master.name} {master.surname or ''}".strip(),
            "phone": master.phone,
            "telegram_id": master.telegram_id,
            "specialization": master.specialization,
            "experience": master.experience,
            "skills_string": master.skills,  # Исходная строка
            "skills": skills_list,  # Массив навыков
            "rating": master.rating,
            "rating_count": master.rating_count,
            "status": master.status,
            "completed_orders": master.completed_orders,
            "active_orders": master.active_orders,
            "notes": master.notes,
            "created_at": master.created_at,
            "updated_at": master.updated_at
        }
        
        return master_data
        
    except Exception as e:
        logger.error(f"❌ Ошибка при получении мастера {master_id}: {e}")
        return None
    finally:
        db.close()