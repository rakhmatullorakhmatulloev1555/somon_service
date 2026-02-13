# app/bot/middleware/error_handler.py
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram import types
import traceback

class ErrorHandlerMiddleware(BaseMiddleware):
    async def on_process_message(self, message: types.Message, data: dict):
        try:
            return await self.process_message(message, data)
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}\n{traceback.format_exc()}")
            await message.answer("❌ Произошла ошибка. Попробуйте позже.")
            raise
    
    async def on_process_callback_query(self, callback: types.CallbackQuery, data: dict):
        try:
            return await self.process_callback(callback, data)
        except Exception as e:
            logger.error(f"Ошибка обработки callback: {e}\n{traceback.format_exc()}")
            await callback.answer("❌ Произошла ошибка", show_alert=True)
            raise

# Добавьте в loader.py:
