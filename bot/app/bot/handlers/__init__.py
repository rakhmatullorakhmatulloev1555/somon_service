# app/bot/handlers/__init__.py
import logging
from .admin import register_admin_handlers
from .client import register_client_handlers
from .master import register_master_handlers
from .common import register_common_handlers
from .parts import register_parts_handlers
from .statistics import register_statistics_handlers

# Настройка логирования
logger = logging.getLogger(__name__)

def register_all_handlers(dp):
    """Регистрация всех обработчиков"""
    register_common_handlers(dp)
    register_client_handlers(dp)
    register_master_handlers(dp)
    register_admin_handlers(dp)
    register_parts_handlers(dp)
    register_statistics_handlers(dp)
    
    logger.info("✅ Все обработчики зарегистрированы")