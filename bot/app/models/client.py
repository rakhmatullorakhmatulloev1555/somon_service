# app/models/client.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String(50), unique=True, index=True, nullable=True)
    username = Column(String(100), nullable=True)
    name = Column(String(200), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Связь с заявками
    tickets = relationship("Ticket", back_populates="client")
    
    # ===== ДОБАВЛЯЕМ СВЯЗЬ С СОБЫТИЯМИ =====
    events = relationship("Event", back_populates="client")
    
    def __repr__(self):
        return f"<Client(id={self.id}, name={self.name})>"