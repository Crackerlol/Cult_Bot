# handlers/ranks.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy import select
from database.base import async_session
from database.models import Disciple
from keyboards.lore_kb import get_main_menu_kb

router = Router()

@router.message(Command("ranks"))
@router.callback_query(F.data == "public_ranks")
async def public_ranks(event: Message | CallbackQuery):
    if isinstance(event, Message):
        message = event
        edit = False
    else:
        message = event.message
        edit = True

    async with async_session() as session:
        result = await session.execute(
            select(Disciple).order_by(Disciple.finger_power.desc())
        )
        disciples = result.scalars().all()

    if not disciples:
        text = "Пока нет ни одного ученика."
    else:
        text = "👥 *Ученики Культа Магистра Естествознания:*\n\n"
        for i, d in enumerate(disciples, 1):
            name = d.nickname or d.full_name or "Неизвестный"
            text += f"{i}. *{name}* — {d.rank}\n"

    if edit:
        try:
            await message.edit_text(text, parse_mode="Markdown", reply_markup=get_main_menu_kb())
        except:
            await event.answer("Список не изменился", show_alert=True)
    else:
        await message.answer(text, parse_mode="Markdown", reply_markup=get_main_menu_kb())