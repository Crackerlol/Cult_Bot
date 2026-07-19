# middlewares/ban.py
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from database.base import async_session
from database.models import Ban

class BanMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        disciple = data.get("disciple")
        if disciple:
            async with async_session() as session:
                result = await session.execute(
                    select(Ban).where(
                        Ban.disciple_id == disciple.id,
                        Ban.is_active == True
                    )
                )
                active_ban = result.scalar_one_or_none()
                if active_ban:
                    # Забанен, не пропускаем
                    if isinstance(event, Message):
                        await event.answer(
                            "⛔ Ты забанен в Культе Магистра.\n"
                            f"Причина: {active_ban.reason or 'не указана'}\n"
                            "Обратись к Магистру."
                        )
                    else:
                        await event.answer("⛔ Ты забанен.", show_alert=True)
                    return
        return await handler(event, data)