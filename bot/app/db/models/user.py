from sqlalchemy import Column, Integer, String, Boolean
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=True)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # admin | master
    password_hash = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
