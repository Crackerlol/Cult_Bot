# handlers/admin.py

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy import select
from database.base import async_session
from database.models import Disciple
from config import settings

router = Router()

def is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.ADMIN_IDS

async def get_all_disciples():
    async with async_session() as session:
        result = await session.execute(select(Disciple).order_by(Disciple.finger_power.desc()))
        return result.scalars().all()

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Ты не обладаешь правами Магистра.")
        return

    disciples = await get_all_disciples()
    if not disciples:
        await message.answer("Нет ни одного ученика.")
        return

    text = "👥 *Ученики Культа (админ-панель):*\n\n"
    for i, d in enumerate(disciples, 1):
        text += (
            f"{i}. {d.nickname or d.full_name} (ID: `{d.telegram_id}`)\n"
            f"   Ранг: {d.rank} | Сила: {d.finger_power:.1f}\n"
            f"   Тренировок: {d.total_workouts} | Инцидентов: {d.dasha_incidents_reported}\n"
            f"   Ник: {d.nickname or 'нет'} | Смена ника: {'да' if d.can_change_nickname else 'нет'}\n\n"
        )

    # Telegram допускает сообщения до 4096 символов, если больше — разобьём
    if len(text) <= 4000:
        await message.answer(text, parse_mode="Markdown")
    else:
        for i in range(0, len(text), 4000):
            await message.answer(text[i:i+4000], parse_mode="Markdown")