# middlewares/dasha_shield.py

import random
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable


class DashaShieldMiddleware(BaseMiddleware):
    """
    Защита от происков Дашки.
    С вероятностью 5% Дашка вмешивается и искажает сообщение бота.
    """
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        # Проверяем, не пытается ли Дашка вмешаться
        if random.random() < 0.05:  # 5% шанс
            if isinstance(event, Message):
                await event.answer(
                    "⚠️ *Внимание!* Дашка пыталась исказить это сообщение, "
                    "но сила Указательного Пальца защитила тебя.\n"
                    "Продолжай качаться, ученик.",
                    parse_mode="Markdown"
                )
        
        return await handler(event, data)