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
from keyboards.profile_kb import get_profile_keyboard
from utils.finger_power import get_next_rank

router = Router()

class Registration(StatesGroup):
    waiting_for_nickname = State()

class NicknameChange(StatesGroup):
    waiting_for_new_nickname = State()

@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username

    async with async_session() as session:
        result = await session.execute(select(Disciple).where(Disciple.telegram_id == telegram_id))
        disciple = result.scalar_one_or_none()

    # 1. Ученик существует и ник уже задан
    if disciple and disciple.nickname:
        keyboard = get_main_menu_kb()
        await message.answer(
            f"🏛 *Культ Магистра Естествознания*\n\n"
            f"С возвращением, *{disciple.nickname}*!\n"
            f"Твой ранг: *{disciple.rank}*\n"
            f"☝️ Сила пальца: *{disciple.finger_power:.2f}*",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        return

    # 2. Ученик существует, но ник не задан (например, создан через тренировку)
    if disciple and not disciple.nickname:
        await state.set_state(Registration.waiting_for_nickname)
        await message.answer(
            "🙏 *Ты уже в Культе, но не представился.*\n"
            "Введи свой ник (или напиши 'пропустить', чтобы использовать имя из Telegram).",
            parse_mode="Markdown"
        )
        return

    # 3. Совсем новый ученик
    await state.set_state(Registration.waiting_for_nickname)
    await message.answer(
        "🙏 *Добро пожаловать в Культ Магистра Естествознания!*\n\n"
        "Как тебя называть, ученик?\n"
        "Введи свой ник (или 'пропустить', чтобы использовать имя из Telegram).",
        parse_mode="Markdown"
    )


@router.message(Registration.waiting_for_nickname)
async def process_nickname(message: Message, state: FSMContext):
    text = message.text.strip()
    telegram_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username

    nickname = full_name if text.lower() == "пропустить" or not text else text

    async with async_session() as session:
        result = await session.execute(select(Disciple).where(Disciple.telegram_id == telegram_id))
        disciple = result.scalar_one_or_none()

        if not disciple:
            # Создаём нового
            disciple = Disciple(
                telegram_id=telegram_id,
                full_name=full_name,
                username=username,
                nickname=nickname,
                can_change_nickname=True
            )
            session.add(disciple)
            message_text = f"✅ *Посвящение пройдено!*\nТвой ник в Культе: *{nickname}*\nДобро пожаловать, ученик. Магистр наблюдает."
        else:
            # Уже существующий, но без ника — просто обновляем ник
            if not disciple.nickname:
                disciple.nickname = nickname
                message_text = f"✅ *Ник сохранён!*\nТвой ник в Культе: *{nickname}*\nДобро пожаловать, ученик. Магистр наблюдает."
            else:
                # Ник уже был (на всякий случай)
                message_text = f"Твой ник уже задан: *{disciple.nickname}*"
        await session.commit()

    await state.clear()
    keyboard = get_main_menu_kb()
    await message.answer(message_text, parse_mode="Markdown", reply_markup=keyboard)

@router.message(Command("setnickname"))
async def set_nickname_command(message: Message, state: FSMContext, disciple: Disciple = None):
    if not disciple:
        await message.answer("Ты не зарегистрирован. /start")
        return
    if not disciple.can_change_nickname:
        await message.answer("⚠️ Ты уже менял ник.")
        return
    await state.set_state(NicknameChange.waiting_for_new_nickname)
    await message.answer(
        "🔄 *Смена ника*\nВведи новый ник. Это можно сделать только один раз.",
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "change_nickname")
async def change_nickname_button(callback: CallbackQuery, state: FSMContext, disciple: Disciple = None):
    if not disciple or not disciple.can_change_nickname:
        await callback.answer("Смена ника недоступна.", show_alert=True)
        return
    await state.set_state(NicknameChange.waiting_for_new_nickname)
    await callback.message.edit_text(
        "🔄 *Смена ника*\nВведи новый ник. Помни: только один раз!",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(NicknameChange.waiting_for_new_nickname)
async def process_nickname_change(message: Message, state: FSMContext, disciple: Disciple = None):
    new_nick = message.text.strip()
    if not new_nick:
        await message.answer("Ник не может быть пустым.")
        return
    async with async_session() as session:
        result = await session.execute(select(Disciple).where(Disciple.telegram_id == message.from_user.id))
        disciple_db = result.scalar_one_or_none()
        if not disciple_db:
            await state.clear()
            await message.answer("Ты не зарегистрирован.")
            return
        disciple_db.nickname = new_nick
        disciple_db.can_change_nickname = False
        await session.commit()
    await state.clear()
    await message.answer(f"✅ *Ник изменён на {new_nick}*", parse_mode="Markdown")
    await message.answer("Изменения сохранены.", reply_markup=get_main_menu_kb())

@router.callback_query(F.data == "my_profile")
async def my_profile(callback: CallbackQuery, disciple: Disciple = None):
    if not disciple:
        await callback.message.edit_text("Ты не зарегистрирован. /start", reply_markup=get_main_menu_kb())
        await callback.answer()
        return
    next_rank, remaining = get_next_rank(disciple.finger_power)
    text = (
        f"👤 *Твой профиль*\n"
        f"🎭 Ник: *{disciple.nickname or 'Не задан'}*\n"
        f"🎖 Ранг: *{disciple.rank}*\n"
        f"☝️ Сила пальца: *{disciple.finger_power:.2f}*\n"
        f"💪 Тренировок: {disciple.total_workouts}\n"
        f"⚠️ Инцидентов: {disciple.dasha_incidents_reported}\n"
        f"📈 До «{next_rank}»: {remaining:.2f} силы\n"
        f"🔄 Смена ника: {'✅ доступна' if disciple.can_change_nickname else '❌ использована'}"
    )
    keyboard = get_profile_keyboard(disciple)
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    except:
        await callback.answer("Профиль не изменился", show_alert=True)
        return
    await callback.answer()