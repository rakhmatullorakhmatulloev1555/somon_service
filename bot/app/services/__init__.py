# app/services/__init__.py
"""
Сервисы для работы с данными
"""

from app.services import part_service
from app.services import ticket_service
from app.services import client_service
from app.services import master_service

__all__ = [
    'part_service',
    'ticket_service',
    'client_service',
    'master_service'
]