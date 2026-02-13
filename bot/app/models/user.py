from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base
from app.database import SessionLocal


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    role = Column(String(20), nullable=False)
    name = Column(String(100), nullable=True)
    telegram_id = Column(String(50), nullable=True)

    # заявки как клиент
    client_tickets = relationship(
        "Ticket",
        foreign_keys="Ticket.client_id",
        back_populates="client"
    )

    # заявки как мастер
    master_tickets = relationship(
        "Ticket",
        foreign_keys="Ticket.master_id",
        back_populates="master"
    )
