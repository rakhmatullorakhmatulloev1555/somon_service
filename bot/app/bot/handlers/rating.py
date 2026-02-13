from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from app.models.master import Master
from app.database import SessionLocal

def register_rating_handlers(dp: Dispatcher):
    @dp.message_handler(Text(equals="⭐ Рейтинги мастеров"))
    async def show_master_ratings_for_clients(message: types.Message):
        """Показать рейтинги мастеров для клиентов"""
        db = SessionLocal()
        
        try:
            masters = db.query(Master).filter(
                Master.rating_count > 0
            ).order_by(Master.rating.desc()).limit(10).all()
            
            if not masters:
                await message.answer("🏆 Пока нет оценок мастеров")
                return
            
            text = "🏆 ЛУЧШИЕ МАСТЕРЫ:\n\n"
            
            for i, master in enumerate(masters, 1):
                rating_stars = "⭐" * int(master.rating) if master.rating > 0 else "暂无评分"
                
                text += f"{i}. {master.name}\n"
                text += f"   🏷 {master.specialization}\n"
                text += f"   ⭐ {master.rating:.2f} ({rating_stars})\n"
                text += f"   📊 {master.rating_count} оценок\n\n"
            
            text += "✨ Оцените работу мастера после завершения вашей заявки!"
            
            await message.answer(text)
                
        except Exception as e:
            print(f"Ошибка при получении рейтингов: {e}")
            await message.answer("❌ Произошла ошибка")
        finally:
            db.close()