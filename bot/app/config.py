import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────
# TELEGRAM
# ─────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

MASTERS_CHAT_ID = int(
    os.getenv("MASTERS_CHAT_ID", "-1000000000000")
)

ADMIN_IDS = list(
    map(int, os.getenv("ADMIN_IDS", "").split(","))
)
# ─────────────────────────────
# DATABASE (MySQL / XAMPP)
# ─────────────────────────────
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "service_bot")

DATABASE_URL = (
    f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ─────────────────────────────
# WEB ADMIN (FastAPI)
# ─────────────────────────────
WEB_ADMIN_LOGIN = os.getenv("WEB_ADMIN_LOGIN", "admin")
WEB_ADMIN_PASSWORD = os.getenv("WEB_ADMIN_PASSWORD", "admin123")
# ─────────────────────────────
# WEB (FastAPI sessions)
# ─────────────────────────────
WEB_SECRET_KEY = os.getenv("WEB_SECRET_KEY", "super-secret-key-change-me")

