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
from utils.disciple_utils import get_disciple, is_banned

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

    # 2. Ученик существует, но ник не задан
    if disciple and not disciple.nickname:
        await state.set_state(Registration.waiting_for_nickname)
        await message.answer(
            "🙏 *Ты уже в Культе, но не представился.*\n"
            "Введи свой ник (или 'пропустить', чтобы использовать имя из Telegram).",
            parse_mode="Markdown"
        )
        return

    # 3. Совсем новый
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
            if not disciple.nickname:
                disciple.nickname = nickname
                message_text = f"✅ *Ник сохранён!*\nТвой ник в Культе: *{nickname}*\nДобро пожаловать, ученик. Магистр наблюдает."
            else:
                message_text = f"Твой ник уже задан: *{disciple.nickname}*"
        await session.commit()

    await state.clear()
    keyboard = get_main_menu_kb()
    await message.answer(message_text, parse_mode="Markdown", reply_markup=keyboard)

@router.message(Command("setnickname"))
async def set_nickname_command(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    disciple = await get_disciple(telegram_id)
    if not disciple:
        await message.answer("Ты не зарегистрирован. /start")
        return
    if not disciple.can_change_nickname:
        await message.answer("⚠️ Ты уже менял ник.")
        return
    await state.set_state(NicknameChange.waiting_for_new_nickname)
    await message.answer("🔄 *Смена ника*\nВведи новый ник. Это можно сделать только один раз.", parse_mode="Markdown")

@router.callback_query(F.data == "change_nickname")
async def change_nickname_button(callback: CallbackQuery, state: FSMContext):
    telegram_id = callback.from_user.id
    disciple = await get_disciple(telegram_id)
    if not disciple:
        await callback.answer("Сначала /start", show_alert=True)
        return
    if not disciple.can_change_nickname:
        await callback.answer("Смена ника уже использована.", show_alert=True)
        return
    await state.set_state(NicknameChange.waiting_for_new_nickname)
    await callback.message.edit_text("🔄 *Смена ника*\nВведи новый ник. Помни: только один раз!", parse_mode="Markdown")
    await callback.answer()

@router.message(NicknameChange.waiting_for_new_nickname)
async def process_nickname_change(message: Message, state: FSMContext):
    new_nick = message.text.strip()
    if not new_nick:
        await message.answer("Ник не может быть пустым.")
        return
    telegram_id = message.from_user.id
    async with async_session() as session:
        result = await session.execute(select(Disciple).where(Disciple.telegram_id == telegram_id))
        disciple = result.scalar_one_or_none()
        if not disciple:
            await state.clear()
            await message.answer("Ты не зарегистрирован.")
            return
        disciple.nickname = new_nick
        disciple.can_change_nickname = False
        await session.commit()
    await state.clear()
    await message.answer(f"✅ *Ник изменён на {new_nick}*", parse_mode="Markdown")
    await message.answer("Изменения сохранены.", reply_markup=get_main_menu_kb())

@router.callback_query(F.data == "my_profile")
async def my_profile(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    disciple = await get_disciple(telegram_id)
    if not disciple:
        # Ответим всплывашкой и не трогаем сообщение, если оно не менялось
        await callback.answer("Ты не зарегистрирован. Введи /start", show_alert=True)
        return

    # Проверка бана для не-админов
    if not disciple.is_admin:
        ban = await is_banned(disciple)
        if ban:
            await callback.answer(f"⛔ Ты забанен: {ban.reason}", show_alert=True)
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

    # Безопасное редактирование: если текст/клавиатура не изменились — просто ответим
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    except Exception:
        await callback.answer("Профиль не изменился", show_alert=True)
        return
    await callback.answer()