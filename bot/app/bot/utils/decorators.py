# app/bot/utils/decorators.py
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def safe_callback():
    """Декоратор для безопасной обработки callback_query"""
    def decorator(func):
        @wraps(func)
        async def wrapper(callback, *args, **kwargs):
            try:
                # Сразу отвечаем на callback
                await callback.answer()
            except:
                pass  # Игнорируем если callback истек
            
            try:
                return await func(callback, *args, **kwargs)
            except Exception as e:
                logger.error(f"Ошибка в callback обработчике {func.__name__}: {e}", exc_info=True)
                # Пытаемся отправить сообщение об ошибке
                try:
                    await callback.bot.send_message(
                        callback.from_user.id,
                        f"❌ Произошла ошибка: {str(e)[:100]}..."
                    )
                except:
                    pass
        return wrapper
    return decorator