# app/__init__.py
"""
Сомон Сервис - Система управления сервисным центром
"""
__version__ = "1.0.0"

# Импортируем модели для создания таблиц
from app.models import (
    Client, Master, Ticket, DeliveryMethod,
    PartCategory, PartSupplier, Part, PartTransaction
)

__all__ = [
    'Client', 'Master', 'Ticket', 'DeliveryMethod',
    'PartCategory', 'PartSupplier', 'Part', 'PartTransaction'
]
