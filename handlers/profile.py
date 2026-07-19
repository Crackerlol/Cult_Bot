# handlers/profile.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from database.base import async_session
from database.models import Disciple
from keyboards.lore_kb import get_main_menu_kb
from utils.finger_power import get_rank, get_next_rank

router = Router()

class Registration(StatesGroup):
    waiting_for_nickname = State()

class NicknameChange(StatesGroup):
    waiting_for_new_nickname = State()

async def get_or_create_disciple(telegram_id: int, full_name: str, username: str = None) -> Disciple:
    async with async_session() as session:
        result = await session.execute(
            select(Disciple).where(Disciple.telegram_id == telegram_id)
        )
        disciple = result.scalar_one_or_none()
        if not disciple:
            disciple = Disciple(
                telegram_id=telegram_id,
                full_name=full_name,
                username=username,
                nickname=None
            )
            session.add(disciple)
            await session.commit()
        return disciple

@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username

    async with async_session() as session:
        result = await session.execute(
            select(Disciple).where(Disciple.telegram_id == telegram_id)
        )
        disciple = result.scalar_one_or_none()

        if not disciple:
            await state.set_state(Registration.waiting_for_nickname)
            await message.answer(
                "🙏 *Добро пожаловать в Культ Магистра Естествознания!*\n\n"
                "Ты ещё не представился. Как тебя называть, ученик?\n"
                "Введи свой ник (или напиши 'пропустить', чтобы использовать имя из Telegram).",
                parse_mode="Markdown"
            )
            return

        if not disciple.nickname:
            await message.answer(
                "🙏 *С возвращением!* Но у тебя ещё нет ника в Культе.\n"
                "Введи желаемый ник (или 'пропустить', чтобы использовать имя Telegram).",
                parse_mode="Markdown"
            )
            await state.set_state(Registration.waiting_for_nickname)
            return

        keyboard = get_main_menu_kb()
        await message.answer(
            f"🏛 *Культ Магистра Естествознания*\n\n"
            f"Ты уже с нами, *{disciple.nickname}*!\n"
            f"Твой ранг: *{disciple.rank}*",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

@router.message(Registration.waiting_for_nickname)
async def process_nickname(message: Message, state: FSMContext):
    text = message.text.strip()
    telegram_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username

    if text.lower() == "пропустить" or not text:
        nickname = full_name
    else:
        nickname = text

    async with async_session() as session:
        result = await session.execute(
            select(Disciple).where(Disciple.telegram_id == telegram_id)
        )
        disciple = result.scalar_one_or_none()

        if not disciple:
            disciple = Disciple(
                telegram_id=telegram_id,
                full_name=full_name,
                username=username,
                nickname=nickname,
                can_change_nickname=True
            )
            session.add(disciple)
        else:
            if not disciple.nickname:
                disciple.nickname = nickname
        await session.commit()

    await state.clear()
    keyboard = get_main_menu_kb()
    await message.answer(
        f"✅ *Посвящение пройдено!*\n"
        f"Твой ник в Культе: *{nickname}*\n"
        f"Добро пожаловать, ученик. Магистр наблюдает.",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@router.message(Command("setnickname"))
async def set_nickname_command(message: Message, state: FSMContext):
    telegram_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(
            select(Disciple).where(Disciple.telegram_id == telegram_id)
        )
        disciple = result.scalar_one_or_none()

        if not disciple:
            await message.answer("Ты не зарегистрирован. Введи /start")
            return

        if not disciple.can_change_nickname:
            await message.answer("⚠️ Ты уже менял ник. Это можно сделать только один раз, ученик.")
            return

        await state.set_state(NicknameChange.waiting_for_new_nickname)
        await message.answer(
            "🔄 *Смена ника*\n\n"
            "Введи новый ник. Помни: это можно сделать *только один раз*.\n"
            "После сохранения изменить будет нельзя.",
            parse_mode="Markdown"
        )

@router.message(NicknameChange.waiting_for_new_nickname)
async def process_nickname_change(message: Message, state: FSMContext):
    new_nick = message.text.strip()
    if not new_nick:
        await message.answer("Ник не может быть пустым. Введи ещё раз.")
        return

    telegram_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(
            select(Disciple).where(Disciple.telegram_id == telegram_id)
        )
        disciple = result.scalar_one_or_none()
        if not disciple:
            await state.clear()
            await message.answer("Ты не зарегистрирован. Введи /start")
            return

        disciple.nickname = new_nick
        disciple.can_change_nickname = False
        await session.commit()

    await state.clear()
    await message.answer(
        f"✅ *Ник изменён на {new_nick}*\n"
        f"Больше ты не сможешь его сменить. Используй с умом.",
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "my_profile")
async def my_profile(callback: CallbackQuery):
    telegram_id = callback.from_user.id

    async with async_session() as session:
        result = await session.execute(
            select(Disciple).where(Disciple.telegram_id == telegram_id)
        )
        disciple = result.scalar_one_or_none()

    if not disciple:
        await callback.message.edit_text(
            "Ты ещё не зарегистрирован. Введи /start",
            reply_markup=get_main_menu_kb()
        )
        await callback.answer()
        return

    next_rank, remaining = get_next_rank(disciple.finger_power)
    debuff_text = "💨 Активен дебафф: Вонь Семёна (-10%)" if disciple.has_semen_debuff else ""

    text = (
        f"👤 *Твой профиль, ученик:*\n\n"
        f"🎭 Ник: *{disciple.nickname or 'Не задан'}*\n"
        f"📛 Имя в TG: {disciple.full_name}\n"
        f"🎖 Ранг: *{disciple.rank}*\n"
        f"☝️ Сила пальца: *{disciple.finger_power:.2f}*\n"
        f"💪 Тренировок: {disciple.total_workouts}\n"
        f"🔢 Подходов: {disciple.total_approaches}\n"
        f"🏋️ Поднято всего: {disciple.total_weight_lifted:.1f} кг\n"
        f"⚠️ Инцидентов с Дашкой: {disciple.dasha_incidents_reported}\n"
        f"💨 Боёв с Семёном: {disciple.semen_battles_won}W / {disciple.semen_battles_lost}L\n"
        f"{debuff_text}\n"
        f"📈 До ранга «{next_rank}»: {remaining:.2f} силы\n"
        f"🔄 Смена ника: {'✅ доступна' if disciple.can_change_nickname else '❌ уже использована'}"
    )

    keyboard = get_main_menu_kb()
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    except:
        await callback.answer("Профиль не изменился", show_alert=True)
        return
    await callback.answer()