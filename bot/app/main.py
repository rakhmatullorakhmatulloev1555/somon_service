# app/main.py
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from app.database import engine, Base
from app.routers import admin_pages, auth, admin, tickets, clients, masters
from app.api.routes import router
from app.api.parts_api import router as parts_api_router  # Импорт API для запчастей
import uvicorn
import asyncio
import threading
import sys
import os

# Создаем FastAPI приложение
app = FastAPI(
    title="Сомон Сервис | Admin",
    description="Панель управления сервисным ботом",
    version="1.0.0"
)

# ============================================
# ИМПОРТ МОДЕЛЕЙ ДЛЯ СОЗДАНИЯ ТАБЛИЦ
# ============================================

# Основные модели
from app.models import ticket, client, master

# Модели для запчастей
from app.models.part import Part, PartCategory, PartSupplier, PartTransaction

# ============================================
# СОЗДАНИЕ ТАБЛИЦ В БАЗЕ ДАННЫХ
# ============================================

try:
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы в базе данных проверены/созданы")
    print("   - Клиенты, Мастера, Заявки")
    print("   - Запчасти, Категории, Поставщики, Транзакции")
except Exception as e:
    print(f"⚠️ Ошибка при создании таблиц: {e}")

# ============================================
# MIDDLEWARE
# ============================================

# Middleware для сессий
app.add_middleware(
    SessionMiddleware,
    secret_key="SUPER_SECRET_ADMIN_KEY_123",
    same_site="lax",
    max_age=3600 * 24  # 24 часа
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# СТАТИЧЕСКИЕ ФАЙЛЫ
# ============================================

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ============================================
# КОРНЕВЫЕ МАРШРУТЫ
# ============================================

@app.get("/")
async def root():
    return RedirectResponse(url="/admin")

@app.get("/health")
async def health_check():
    return {"status": "ok", "tables": "created"}

# ============================================
# ПОДКЛЮЧЕНИЕ ВСЕХ РОУТЕРОВ
# ============================================

app.include_router(router)                 # Основные маршруты
app.include_router(clients.router)         # Клиенты
app.include_router(admin_pages.router)     # Страницы админки
app.include_router(auth.router)            # Аутентификация
app.include_router(tickets.router)         # Заявки
app.include_router(admin.router)           # Админка
app.include_router(masters.router)         # Мастера
app.include_router(parts_api_router)       # API для запчастей

# ============================================
# ФУНКЦИИ ДЛЯ ЗАПУСКА
# ============================================

def run_telegram_bot():
    """Запуск Telegram бота в отдельном потоке"""
    try:
        import asyncio
        import sys
        
        # Устанавливаем event loop policy для Windows
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        from app.bot.loader import start_bot
        from app.bot.loader import logger
        
        logger.info("🤖 Запуск Telegram бота...")
        
        # Запускаем бота
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_bot())
        
    except KeyboardInterrupt:
        logger.info("🤖 Telegram бот остановлен")
    except Exception as e:
        logger.error(f"🤖 Ошибка в Telegram боте: {e}")

def run_web_admin():
    """Запуск веб-админки"""
    try:
        import uvicorn
        
        print("\n" + "="*60)
        print("🌐 ВЕБ-АДМИНКА ЗАПУЩЕНА")
        print("="*60)
        print("📍 Основной адрес: http://localhost:8000")
        print("📍 Страница входа: http://localhost:8000/login")
        print("📍 Админ панель: http://localhost:8000/admin")
        print("\n📦 УПРАВЛЕНИЕ ЗАПЧАСТЯМИ:")
        print("📍 Склад запчастей: http://localhost:8000/admin/parts")
        print("📍 Категории: http://localhost:8000/admin/categories")
        print("📍 Поставщики: http://localhost:8000/admin/suppliers")
        print("\n📊 API ЭНДПОИНТЫ:")
        print("📍 Запчасти: http://localhost:8000/api/parts")
        print("📍 Категории: http://localhost:8000/api/parts/categories")
        print("📍 Поставщики: http://localhost:8000/api/parts/suppliers/all")
        print("📍 Статистика: http://localhost:8000/api/parts/stats/all")
        print("📍 Документация API: http://localhost:8000/docs")
        print("\n👤 ДЕМО-ДОСТУП:")
        print("   Логин: admin / Пароль: admin123")
        print("   Логин: manager / Пароль: manager123")
        print("="*60 + "\n")
        
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        print(f"🌐 Ошибка в веб-админке: {e}")

# Основная функция запуска
def main():
    """Главная функция запуска бота и веб-админки"""
    print("\n" + "="*60)
    print("🚀 ЗАПУСК СИСТЕМЫ СОМОН СЕРВИС")
    print("="*60)
    print("📦 ЗАГРУЖЕННЫЕ МОДУЛИ:")
    print("   ✅ Клиенты")
    print("   ✅ Мастера")
    print("   ✅ Заявки")
    print("   ✅ Запчасти")
    print("   ✅ Категории запчастей")
    print("   ✅ Поставщики")
    print("   ✅ Транзакции склада")
    print("="*60 + "\n")
    
    # Запускаем Telegram бот в отдельном потоке
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем веб-админку в основном потоке
    run_web_admin()

if __name__ == "__main__":
    main()