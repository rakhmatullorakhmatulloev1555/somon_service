# test_master.py
from app.models.master import Master
import inspect

print("Поля модели Master:")
for name, obj in inspect.getmembers(Master):
    if not name.startswith('_'):
        print(f"  {name}: {type(obj)}")

print("\nАтрибуты таблицы:")
print(Master.__table__.columns.keys())