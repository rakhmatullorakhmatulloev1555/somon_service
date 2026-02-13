from app.models.client import Client



def get_or_create_client(db, telegram_user):

    client = db.query(Client).filter(
        Client.telegram_id == telegram_user.id
    ).first()

    if client:
        return client

    client = Client(
        telegram_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
        last_name=telegram_user.last_name
    )

    db.add(client)
    db.commit()
    db.refresh(client)

    return client