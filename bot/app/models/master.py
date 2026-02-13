# app/models/master.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Master(Base):
    __tablename__ = "masters"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String(50), unique=True, index=True, nullable=True)
    name = Column(String(100), nullable=False)
    surname = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    specialization = Column(String(200), nullable=True)
    experience = Column(Integer, default=0)
    skills = Column(Text, nullable=True)
    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    status = Column(String(20), default="active")
    completed_orders = Column(Integer, default=0)
    active_orders = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Связь с заявками
    tickets = relationship("Ticket", back_populates="master")
    
    # ===== ДОБАВЛЯЕМ СВЯЗЬ С СОБЫТИЯМИ =====
    events = relationship("Event", back_populates="master")
    
    def __repr__(self):
        return f"<Master(id={self.id}, name={self.name} {self.surname or ''})>"