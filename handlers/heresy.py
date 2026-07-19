# handlers/heresy.py

import random
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy import select
from database.base import async_session
from database.models import Disciple, DashaIncident
from keyboards.heresy_kb import get_dasha_report_kb, get_semen_battle_kb
from keyboards.lore_kb import get_main_menu_kb

router = Router()


@router.message(Command("report"))
async def report_command(message: Message):
    """Команда /report — доложить о Дашке."""
    keyboard = get_dasha_report_kb()
    await message.answer(
        "⚠️ *Доклад о происках Дашки*\n\n"
        "Что случилось, ученик?",
        parse_mode="Markdown",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "report_dasha")
async def report_dasha(callback: CallbackQuery):
    """Кнопка репорта о Дашке."""
    keyboard = get_dasha_report_kb()
    await callback.message.edit_text(
        "⚠️ *Доклад о происках Дашки*\n\n"
        "Что случилось, ученик?",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "dasha_sighting")
async def dasha_sighting(callback: CallbackQuery):
    """Видел Дашку."""
    await save_incident(callback, "dasha_sighting", 3, "Ученик заметил Дашку поблизости")
    await callback.message.edit_text(
        "👁️ *Дашка замечена!*\n\n"
        "Магистр предупреждён. Держись подальше от тёмных углов.\n"
        "Продолжай тренировки — сила пальца защитит тебя.",
        parse_mode="Markdown",
        reply_markup=get_main_menu_kb()
    )
    await callback.answer("⚠️ Дашка рядом...")


@router.callback_query(F.data == "semen_attack")
async def semen_attack(callback: CallbackQuery):
    """Атака Семёна — мини-игра."""
    keyboard = get_semen_battle_kb()
    await callback.message.edit_text(
        "💨 *АТАКА СЕМЁНА!*\n\n"
        "Чувствуешь этот запах? Семён рядом!\n"
        "Выбери действие, ученик, и поторопись!\n\n"
        "😤 Задержать дыхание — защита\n"
        "☝️ Сила Пальца — контратака\n"
        "🏃 Бежать — сбежать с поля боя",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "hold_breath")
async def hold_breath(callback: CallbackQuery):
    """Задержать дыхание — 70% шанс успеха."""
    success = random.random() < 0.7
    
    if success:
        result = (
            "😤 *Ты задержал дыхание!*\n\n"
            "Вонь Семёна не достигла тебя. Ты выстоял.\n"
            "Семён, разочарованный, уходит в тень.\n"
            "☝️ +5 к силе духа!"
        )
        debuff = False
    else:
        result = (
            "💨 *Вонь пробилась!*\n\n"
            "Ты не смог сдержать дыхание. Семён злорадствует.\n"
            "⚠️ Дебафф: -10% к следующей тренировке."
        )
        debuff = True
    
    await handle_semen_battle_result(callback, success, debuff, result)


@router.callback_query(F.data == "finger_attack")
async def finger_attack(callback: CallbackQuery):
    """Сила Пальца — 50% шанс успеха, но больше награда."""
    success = random.random() < 0.5
    
    if success:
        result = (
            "☝️ *СИЛА ПАЛЬЦА АКТИВИРОВАНА!*\n\n"
            "Ты направил указательный палец на Семёна!\n"
            "Вонючий прихвостень отброшен назад!\n"
            "Дашка в ярости, но Семён повержен.\n"
            "🏆 +15 к силе пальца за победу!"
        )
        debuff = False
    else:
        result = (
            "💨 *Семён увернулся!*\n\n"
            "Сила пальца дала осечку. Семён пустил особо едкую волну.\n"
            "⚠️ Двойной дебафф: -20% к следующей тренировке."
        )
        debuff = True
    
    await handle_semen_battle_result(callback, success, debuff, result)


@router.callback_query(F.data == "run_away")
async def run_away(callback: CallbackQuery):
    """Бежать — 90% шанс избежать дебаффа, но нет награды."""
    success = random.random() < 0.9
    
    if success:
        result = (
            "🏃 *Ты сбежал!*\n\n"
            "Быстрые ноги спасли тебя от вони Семёна.\n"
            "Это не трусость, а тактическое отступление.\n"
            "Но Магистр хмурится..."
        )
        debuff = False
    else:
        result = (
            "💨 *Не успел!*\n\n"
            "Семён оказался быстрее. Вонь настигла тебя.\n"
            "⚠️ Дебафф: -10% к следующей тренировке."
        )
        debuff = True
    
    await handle_semen_battle_result(callback, success, debuff, result)


async def handle_semen_battle_result(callback: CallbackQuery, success: bool, debuff: bool, result: str):
    """Обрабатывает результат боя с Семёном."""
    telegram_id = callback.from_user.id
    
    async with async_session() as session:
        result_query = await session.execute(
            select(Disciple).where(Disciple.telegram_id == telegram_id)
        )
        disciple = result_query.scalar_one_or_none()
        
        if not disciple:
            await callback.answer("Сначала нужна тренировка, ученик.")
            return
        
        # Записываем инцидент
        incident = DashaIncident(
            disciple_id=disciple.id,
            incident_type="semen_attack",
            description="Бой с Семёном",
            threat_level=6,
            involved_semen=True,
            semen_defeated=success,
        )
        session.add(incident)
        
        # Обновляем статистику
        disciple.dasha_incidents_reported += 1
        if success:
            disciple.semen_battles_won += 1
            if not debuff:
                disciple.finger_power += 5
        else:
            disciple.semen_battles_lost += 1
        
        # Применяем дебафф если нужно
        if debuff:
            disciple.has_semen_debuff = True
            disciple.semen_debuff_until = datetime.utcnow() + timedelta(hours=24)
        
        await session.commit()
    
    await callback.message.edit_text(
        result + "\n\nВыбери дальнейшее действие:",
        parse_mode="Markdown",
        reply_markup=get_main_menu_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "light_flicker")
async def light_flicker(callback: CallbackQuery):
    """Мигание фонаря."""
    await save_incident(callback, "light_flicker", 4, "Фонарь мигнул у дома ученика")
    await callback.message.edit_text(
        "💡 *Фонарь мигнул!*\n\n"
        "Это проделки Дашки или Семён подошёл слишком близко?\n"
        "Будь начеку, ученик. Сила пальца поможет зажечь свет вновь.",
        parse_mode="Markdown",
        reply_markup=get_main_menu_kb()
    )
    await callback.answer("💡 Свет погас...")


@router.callback_query(F.data == "major_incident")
async def major_incident(callback: CallbackQuery):
    """Крупный инцидент."""
    await save_incident(callback, "major_incident", 8, "Крупный инцидент с Дашкой")
    await callback.message.edit_text(
        "🆘 *КРУПНЫЙ ИНЦИДЕНТ!*\n\n"
        "Дашка активизировалась! Магистр оповещён.\n"
        "Все ученики должны удвоить тренировки.\n"
        "Время заморозить её происки силой пальца!",
        parse_mode="Markdown",
        reply_markup=get_main_menu_kb()
    )
    await callback.answer("🆘 Магистр оповещён!")


async def save_incident(callback: CallbackQuery, incident_type: str, threat_level: int, description: str):
    """Сохраняет инцидент с Дашкой в базу."""
    telegram_id = callback.from_user.id
    
    async with async_session() as session:
        result = await session.execute(
            select(Disciple).where(Disciple.telegram_id == telegram_id)
        )
        disciple = result.scalar_one_or_none()
        
        if not disciple:
            return
        
        incident = DashaIncident(
            disciple_id=disciple.id,
            incident_type=incident_type,
            description=description,
            threat_level=threat_level,
            involved_semen=False,
            semen_defeated=False,
        )
        session.add(incident)
        
        disciple.dasha_incidents_reported += 1
        await session.commit()