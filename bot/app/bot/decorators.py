# декоратор в app/bot/decorators.py
from functools import wraps
from aiogram import types
from app.bot.config import ADMIN_IDS

def admin_required(func):
    @wraps(func)
    async def wrapper(message: types.Message | types.CallbackQuery, *args, **kwargs):
        user_id = message.from_user.id
        if user_id not in ADMIN_IDS:
            if isinstance(message, types.CallbackQuery):
                await message.answer("⛔ Доступно только администраторам", show_alert=True)
            else:
                await message.answer("⛔ Доступно только администраторам")
            return
        return await func(message, *args, **kwargs)
    return wrapper

# Использование:
@dp.message_handler(commands=["admin"])
@admin_required
async def admin_panel(message: types.Message):
    await message.answer("⚙️ Админ панель", reply_markup=admin_menu())