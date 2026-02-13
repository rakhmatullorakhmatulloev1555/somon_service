# app/models/event.py
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    event_type = Column(String(50), nullable=False)  # repair, delivery, meeting, appointment, other
    color = Column(String(50), default="primary")
    
    # Дата и время
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    is_all_day = Column(Boolean, default=False)
    
    # Связи
    master_id = Column(Integer, ForeignKey("masters.id"), nullable=True)
    master = relationship("Master", back_populates="events")
    
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    client = relationship("Client", back_populates="events")
    
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    ticket = relationship("Ticket", back_populates="events")
    
    # Детали
    description = Column(Text, nullable=True)
    location = Column(String(200), nullable=True)
    
    # Уведомления
    notification_sent = Column(Boolean, default=False)
    reminder_minutes = Column(Integer, default=30)
    
    # Метаданные
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Event(id={self.id}, title={self.title}, date={self.start_date})>"