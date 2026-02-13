# app/bot/config.py
import os
import re
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Исправьте строку с ADMIN_IDS_STR - она неправильная
    ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "8296004753,6284411828")  # НЕ 8296004753,6284411828
    
    # Правильное разбиение
    ADMIN_IDS = []
    if ADMIN_IDS_STR:
        for admin_id in ADMIN_IDS_STR.split(','):
            admin_id = admin_id.strip().strip('[]')  # Убираем возможные скобки
            if admin_id and admin_id.isdigit():
                ADMIN_IDS.append(int(admin_id))
    
    # Если после очистки список пуст, используем значения по умолчанию
    if not ADMIN_IDS:
        ADMIN_IDS = [8296004753, 6284411828]
    
    # Остальные настройки
    BOT_TOKEN = os.getenv("BOT_TOKEN", "8247611540:AAG1Cl7Ath8gMkblDJrBvCYaMqnSJU6VHjs")
    MASTER_GROUP_ID = int(os.getenv("MASTER_GROUP_ID", -1003664975361))
    
    # ID мастеров
    MASTER_IDS = [8198019891]

config = Config()

# Также экспортируем как отдельные переменные для обратной совместимости
BOT_TOKEN = config.BOT_TOKEN
ADMIN_IDS = config.ADMIN_IDS
MASTER_IDS = config.MASTER_IDS
MASTER_GROUP_ID = config.MASTER_GROUP_ID