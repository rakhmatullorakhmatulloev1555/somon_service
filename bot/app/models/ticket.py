# app/models/ticket.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

# Импортируем Base
from app.database import Base

# Enum для способа получения
class DeliveryMethod(enum.Enum):
    PICKUP = "pickup"  # Клиент принес сам
    DELIVERY = "delivery"  # Курьерская доставка
    WALKIN = "walkin"  # Клиент пришел без заявки

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    master_id = Column(Integer, ForeignKey("masters.id"), nullable=True)
    
    # Способ получения
    delivery_method = Column(
        Enum(DeliveryMethod),
        default=DeliveryMethod.PICKUP,
        nullable=False
    )
    
    # Поля для доставки
    delivery_address = Column(Text, nullable=True)
    delivery_phone = Column(String(20), nullable=True)
    delivery_date = Column(DateTime, nullable=True)
    delivery_notes = Column(Text, nullable=True)
    
    # Поля для клиента в сервисе
    walkin_name = Column(String(100), nullable=True)
    walkin_phone = Column(String(20), nullable=True)
    
    # Существующие поля - УДАЛЯЕМ total_price и completed_at
    branch = Column(String(100))
    category = Column(String(100))
    subcategory = Column(String(100))
    brand = Column(String(100))
    problem = Column(Text)
    photos = Column(Text)  # JSON
    urgency = Column(String(50))
    status = Column(String(50), default="Новая")
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Связи с другими моделями
    client = relationship("Client", back_populates="tickets")
    master = relationship("Master", back_populates="tickets")
    
    # Связь с запчастями
    part_transactions = relationship(
        "PartTransaction", 
        back_populates="ticket",
        cascade="all, delete-orphan",
        foreign_keys="[PartTransaction.ticket_id]"
    )
    
    # Связь с событиями
    events = relationship(
        "Event", 
        back_populates="ticket",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Ticket(id={self.id}, status={self.status})>"