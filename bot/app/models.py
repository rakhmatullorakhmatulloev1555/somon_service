from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, TIMESTAMP
)
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String(255))
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="client")
    # specialty = Column(String(50), nullable=True)

    client_tickets = relationship(
        "Ticket",
        foreign_keys="Ticket.client_id",
        back_populates="client"
    )

    master_tickets = relationship(
        "Ticket",
        foreign_keys="Ticket.master_id",
        back_populates="master"
    )


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True)

    client_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    master_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    branch_id = Column(Integer, nullable=True)

    device_type = Column(String(255))
    brand_model = Column(String(255))
    problem_desc = Column(Text)
    urgency = Column(String(50))
    status = Column(String(50), default="new")

    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)

    client = relationship("User", foreign_keys=[client_id], back_populates="client_tickets")
    master = relationship("User", foreign_keys=[master_id], back_populates="master_tickets")
    comment = Column(Text, nullable=True)
    

     # 👇 НОВОЕ
    rating = Column(Integer, nullable=True)      # 1–5
    review = Column(Text, nullable=True)          # текст отзыва

    photos = relationship(
        "TicketPhoto",
        back_populates="ticket",
        cascade="all, delete-orphan"
    )


class TicketPhoto(Base):
    __tablename__ = "ticket_photos"

    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"))
    file_id = Column(String(255))

    ticket = relationship("Ticket", back_populates="photos")
