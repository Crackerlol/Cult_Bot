# utils/disciple_utils.py
from sqlalchemy import select
from database.base import async_session
from database.models import Disciple, Ban

async def get_disciple(telegram_id: int) -> Disciple | None:
    """Получает ученика по Telegram ID или None."""
    async with async_session() as session:
        result = await session.execute(
            select(Disciple).where(Disciple.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

async def is_banned(disciple: Disciple) -> Ban | None:
    """Возвращает активный бан или None, если ученик не забанен."""
    async with async_session() as session:
        result = await session.execute(
            select(Ban).where(
                Ban.disciple_id == disciple.id,
                Ban.is_active == True
            )
        )
        return result.scalar_one_or_none()