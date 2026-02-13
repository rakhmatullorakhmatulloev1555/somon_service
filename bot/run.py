# run.py (в корне проекта)
#!/usr/bin/env python
"""
Запуск всей системы: Telegram бота + веб-админка
"""

import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 50)
    print("🚀 SERVICE BOT SYSTEM")
    print("=" * 50)
    print("Запуск системы...")
    print("")
    print("🌐 Веб-админка: http://localhost:8000")
    print("👤 Логин: admin / admin123")
    print("🤖 Telegram бот: запущен в фоновом режиме")
    print("=" * 50)
    
    # Запускаем основной файл
    from app.main import main as app_main
    app_main()

if __name__ == "__main__":
    main()