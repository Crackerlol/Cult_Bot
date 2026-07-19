# middlewares/disciple_loader.py
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from database.base import async_session
from database.models import Disciple

class DiscipleLoaderMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id
        async with async_session() as session:
            result = await session.execute(
                select(Disciple).where(Disciple.telegram_id == user_id)
            )
            disciple = result.scalar_one_or_none()
        data["disciple"] = disciple
        return await handler(event, data)