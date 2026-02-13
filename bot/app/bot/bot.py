# from aiogram import Bot
# from aiogram.dispatcher import Dispatcher
# from aiogram.contrib.fsm_storage.memory import MemoryStorage

# from app.bot.config import BOT_TOKEN

# bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
# storage = MemoryStorage()
# dp = Dispatcher(bot, storage=storage)

# from app.bot.config import ADMIN_IDS, MASTER_IDS, MASTER_GROUP_ID, BOT_TOKEN

# # 🔥 TOKEN

# BOT_TOKEN="8247611540:AAG1Cl7Ath8gMkblDJrBvCYaMqnSJU6VHjs"

# # ✅ создаём bot
# bot = Bot(token=BOT_TOKEN)

# # ✅ создаём dispatcher
# dp = Dispatcher(bot, storage=storage)

# # подключаем handlers ПОСЛЕ создания dp
import os
# app/bot/bot.py
from app.bot.loader import bot, dp

MASTER_GROUP_ID = int(os.getenv("MASTER_GROUP_ID", -1003664975361))  # Замените на ваш ID

# Экспортируем для обратной совместимости
__all__ = ['bot', 'dp']

