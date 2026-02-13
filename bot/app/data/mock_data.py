# ===== Мастера =====
MASTERS = [
    {"id": 1, "name": "Мастер по заправке картриджей", "role": "cartridge"},
    {"id": 2, "name": "Мастер принтеров", "role": "printer"},
    {"id": 3, "name": "Мастер ПК и ноутбуков", "role": "pc"},
    {"id": 4, "name": "Старший мастер", "role": "senior"},
]
 
# ===== Заявки =====
TICKETS = [
    {
        "id": 1,
        "title": "Не включается ПК",
        "category": "ПК / Ноутбук",
        "status": "Новая",
        "master_id": None
    },
    {
        "id": 2,
        "title": "Заправка картриджа",
        "category": "Принтер",
        "status": "В работе",
        "master_id": 1
    }
]

STATUS_CLASS = {
    "Новая": "new",
    "Назначена": "work",
    "В работе": "work",
    "Готово": "done",
}

USERS = [
    {
        "id": 1,
        "username": "admin",
        "password": "admin123",
        "role": "admin"
    },
    {
        "id": 2,
        "username": "master_pc",
        "password": "123",
        "role": "master",
        "master_id": 1
    }
]