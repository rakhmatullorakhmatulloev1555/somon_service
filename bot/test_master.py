# test_master.py
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.master import Master
from sqlalchemy import inspect

# Создаем объект инспектора для модели
inspector = inspect(Master)

print("=== ПОЛЯ МОДЕЛИ MASTER ===")
print("Имя таблицы:", Master.__tablename__)
print("\nКолонки таблицы:")

for column in inspector.columns:
    print(f"  - {column.name}: {column.type}")

print("\n=== ВСЕ АТРИБУТЫ МОДЕЛИ ===")
for attr_name in dir(Master):
    if not attr_name.startswith('_') and not callable(getattr(Master, attr_name)):
        print(f"  - {attr_name}")