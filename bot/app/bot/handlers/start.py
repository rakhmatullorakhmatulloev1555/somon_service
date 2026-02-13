from aiogram import types
from aiogram.dispatcher import Dispatcher
from app.bot.config import ADMIN_IDS
from .common import admin_main_keyboard, client_main_keyboard

def register_start_handlers(dp: Dispatcher):
    @dp.message_handler(commands=['start'])
    async def cmd_start(message: types.Message):
        """Обработчик команды /start"""
        if message.from_user.id in ADMIN_IDS:
            await message.answer(
                "👋 Добро пожаловать, администратор!\n\n"
                "Вы можете управлять заявками и просматривать рейтинги мастеров.",
                reply_markup=admin_main_keyboard()
            )
        else:
            await message.answer(
                "👋 Добро пожаловать в сервисный центр!\n\n"
                "Здесь вы можете создавать заявки на ремонт и просматривать рейтинги мастеров.",
                reply_markup=client_main_keyboard()
            )