from sqlalchemy.orm import Session
from app.models.client import Client


def get_or_create_client(db: Session, user):
    client = db.query(Client).filter(
        Client.telegram_id == str(user.id)
    ).first()

    if client:
        return client

    client = Client(
        telegram_id=str(user.id),
        name=user.full_name,
        username=user.username
    )

    db.add(client)
    db.commit()
    db.refresh(client)

    return client
