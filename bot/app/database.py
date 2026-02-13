# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# XAMPP MySQL connection
DATABASE_URL = "mysql+pymysql://root:@localhost/service_center"

# Создаем базовый класс для моделей
Base = declarative_base()

# Создаем движок
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ✅ FASTAPI dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()