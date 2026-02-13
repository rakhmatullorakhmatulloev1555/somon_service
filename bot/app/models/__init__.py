# app/models/__init__.py
"""
Инициализация моделей в правильном порядке
"""

# Сначала базовые модели без зависимостей
from app.models.client import Client
from app.models.master import Master

# Затем модели, которые зависят от Client и Master
from app.models.ticket import Ticket, DeliveryMethod

# Затем модели запчастей
from app.models.part import PartCategory, PartSupplier, Part, PartTransaction

# Затем модель событий (зависит от всех выше)
from app.models.event import Event

# Экспортируем все модели
__all__ = [
    'Client',
    'Master',
    'Ticket',
    'DeliveryMethod',
    'PartCategory',
    'PartSupplier',
    'Part',
    'PartTransaction',
    'Event'  # Добавляем Event
]
