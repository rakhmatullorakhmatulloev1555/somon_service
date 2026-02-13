from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Ticket

async def get_all_tickets(session: AsyncSession):
    result = await session.execute(
        select(Ticket).order_by(Ticket.created_at.desc())
    )
    return result.scalars().all()

async def get_master_tickets(
    session: AsyncSession,
    master_id: int
):
    result = await session.execute(
        select(Ticket).where(Ticket.master_id == master_id)
    )
    return result.scalars().all()
