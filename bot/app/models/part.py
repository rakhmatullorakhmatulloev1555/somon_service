# app/models/part.py
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class PartCategory(Base):
    """Категория запчастей"""
    __tablename__ = "part_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), default="fas fa-box")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    parts = relationship("Part", back_populates="category")
    
    def __repr__(self):
        return f"<PartCategory(id={self.id}, name={self.name})>"

class PartSupplier(Base):
    """Поставщик запчастей"""
    __tablename__ = "part_suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    contact_person = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    parts = relationship("Part", back_populates="supplier")
    
    def __repr__(self):
        return f"<PartSupplier(id={self.id}, name={self.name})>"

class Part(Base):
    """Запчасть"""
    __tablename__ = "parts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    sku = Column(String(50), unique=True, index=True, nullable=False)
    brand = Column(String(100), nullable=True)
    
    # Цены
    purchase_price = Column(Float, default=0)
    sale_price = Column(Float, default=0)
    
    # Склад
    stock = Column(Integer, default=0)
    min_stock = Column(Integer, default=5)
    location = Column(String(100), nullable=True)
    
    # Категория
    category_id = Column(Integer, ForeignKey("part_categories.id"))
    category = relationship("PartCategory", back_populates="parts")
    
    # Поставщик
    supplier_id = Column(Integer, ForeignKey("part_suppliers.id"), nullable=True)
    supplier = relationship("PartSupplier", back_populates="parts")
    
    # Описание
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    
    # Статус
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    transactions = relationship("PartTransaction", back_populates="part")
    
    @property
    def status(self):
        if self.stock <= 0:
            return "out"
        elif self.stock < self.min_stock:
            return "low"
        elif self.stock < self.min_stock * 2:
            return "medium"
        else:
            return "high"
    
    @property
    def total_value(self):
        return self.purchase_price * self.stock
    
    def __repr__(self):
        return f"<Part(id={self.id}, name={self.name}, sku={self.sku})>"

class PartTransaction(Base):
    """Движение запчастей (приход/расход)"""
    __tablename__ = "part_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    part_id = Column(Integer, ForeignKey("parts.id"))
    part = relationship("Part", back_populates="transactions")
    
    transaction_type = Column(String(20))  # in, out, return
    quantity = Column(Integer, default=1)
    price = Column(Float, default=0)
    
    # Связь с заявкой
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    ticket = relationship("Ticket", back_populates="part_transactions")
    
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PartTransaction(id={self.id}, part_id={self.part_id}, type={self.transaction_type}, qty={self.quantity})>"