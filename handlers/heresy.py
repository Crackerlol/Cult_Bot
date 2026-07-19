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
from utils.disciple_utils import get_disciple, is_banned

router = Router()

async def check_access(user_id: int) -> Disciple | None:
    disciple = await get_disciple(user_id)
    if not disciple:
        return None
    if not disciple.is_admin:
        ban = await is_banned(disciple)
        if ban:
            return None
    return disciple

@router.message(Command("report"))
async def report_command(message: Message):
    if not await check_access(message.from_user.id):
        await message.answer("⛔ Недоступно. Проверь /start.")
        return
    keyboard = get_dasha_report_kb()
    await message.answer("⚠️ *Доклад о происках Дашки*\n\nЧто случилось, ученик?", parse_mode="Markdown", reply_markup=keyboard)

@router.callback_query(F.data == "report_dasha")
async def report_dasha(callback: CallbackQuery):
    if not await check_access(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    keyboard = get_dasha_report_kb()
    await callback.message.edit_text("⚠️ *Доклад о происках Дашки*\n\nЧто случилось, ученик?", parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "dasha_sighting")
async def dasha_sighting(callback: CallbackQuery):
    if not await check_access(callback.from_user.id):
        return await callback.answer("Нет доступа")
    await save_incident(callback, "dasha_sighting", 3, "Ученик заметил Дашку поблизости")
    await callback.message.edit_text(
        "👁️ *Дашка замечена!*\n\nМагистр предупреждён. Держись подальше от тёмных углов.\nПродолжай тренировки — сила пальца защитит тебя.",
        parse_mode="Markdown",
        reply_markup=get_main_menu_kb()
    )
    await callback.answer()

@router.callback_query(F.data == "semen_attack")
async def semen_attack(callback: CallbackQuery):
    if not await check_access(callback.from_user.id):
        return await callback.answer("Нет доступа")
    keyboard = get_semen_battle_kb()
    await callback.message.edit_text(
        "💨 *АТАКА СЕМЁНА!*\n\nЧувствуешь этот запах? Семён рядом!\nВыбери действие, ученик, и поторопись!\n\n"
        "😤 Задержать дыхание — защита\n☝️ Сила Пальца — контратака\n🏃 Бежать — сбежать с поля боя",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data == "hold_breath")
async def hold_breath(callback: CallbackQuery):
    if not await check_access(callback.from_user.id):
        return await callback.answer("Нет доступа")
    success = random.random() < 0.7
    if success:
        result = "😤 *Ты задержал дыхание!*\n\nВонь Семёна не достигла тебя. Ты выстоял.\nСемён, разочарованный, уходит в тень.\n☝️ +5 к силе духа!"
        debuff = False
    else:
        result = "💨 *Вонь пробилась!*\n\nТы не смог сдержать дыхание. Семён злорадствует.\n⚠️ Дебафф: -10% к следующей тренировке."
        debuff = True
    await handle_semen_battle_result(callback, success, debuff, result)

@router.callback_query(F.data == "finger_attack")
async def finger_attack(callback: CallbackQuery):
    if not await check_access(callback.from_user.id):
        return await callback.answer("Нет доступа")
    success = random.random() < 0.5
    if success:
        result = "☝️ *СИЛА ПАЛЬЦА АКТИВИРОВАНА!*\n\nТы направил указательный палец на Семёна!\nВонючий прихвостень отброшен назад!\nДашка в ярости, но Семён повержен.\n🏆 +15 к силе пальца за победу!"
        debuff = False
    else:
        result = "💨 *Семён увернулся!*\n\nСила пальца дала осечку. Семён пустил особо едкую волну.\n⚠️ Двойной дебафф: -20% к следующей тренировке."
        debuff = True
    await handle_semen_battle_result(callback, success, debuff, result)

@router.callback_query(F.data == "run_away")
async def run_away(callback: CallbackQuery):
    if not await check_access(callback.from_user.id):
        return await callback.answer("Нет доступа")
    success = random.random() < 0.9
    if success:
        result = "🏃 *Ты сбежал!*\n\nБыстрые ноги спасли тебя от вони Семёна.\nЭто не трусость, а тактическое отступление.\nНо Магистр хмурится..."
        debuff = False
    else:
        result = "💨 *Не успел!*\n\nСемён оказался быстрее. Вонь настигла тебя.\n⚠️ Дебафф: -10% к следующей тренировке."
        debuff = True
    await handle_semen_battle_result(callback, success, debuff, result)

async def handle_semen_battle_result(callback: CallbackQuery, success: bool, debuff: bool, result: str):
    telegram_id = callback.from_user.id
    async with async_session() as session:
        result_query = await session.execute(select(Disciple).where(Disciple.telegram_id == telegram_id))
        disciple = result_query.scalar_one_or_none()
        if not disciple:
            await callback.answer("Сначала /start")
            return

        incident = DashaIncident(
            disciple_id=disciple.id,
            incident_type="semen_attack",
            description="Бой с Семёном",
            threat_level=6,
            involved_semen=True,
            semen_defeated=success,
        )
        session.add(incident)

        disciple.dasha_incidents_reported += 1
        if success:
            disciple.semen_battles_won += 1
            if not debuff:
                disciple.finger_power += 5
        else:
            disciple.semen_battles_lost += 1

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
    if not await check_access(callback.from_user.id):
        return await callback.answer("Нет доступа")
    await save_incident(callback, "light_flicker", 4, "Фонарь мигнул у дома ученика")
    await callback.message.edit_text(
        "💡 *Фонарь мигнул!*\n\nЭто проделки Дашки или Семён подошёл слишком близко?\nБудь начеку, ученик. Сила пальца поможет зажечь свет вновь.",
        parse_mode="Markdown",
        reply_markup=get_main_menu_kb()
    )
    await callback.answer()

@router.callback_query(F.data == "major_incident")
async def major_incident(callback: CallbackQuery):
    if not await check_access(callback.from_user.id):
        return await callback.answer("Нет доступа")
    await save_incident(callback, "major_incident", 8, "Крупный инцидент с Дашкой")
    await callback.message.edit_text(
        "🆘 *КРУПНЫЙ ИНЦИДЕНТ!*\n\nДашка активизировалась! Магистр оповещён.\nВсе ученики должны удвоить тренировки.\nВремя заморозить её происки силой пальца!",
        parse_mode="Markdown",
        reply_markup=get_main_menu_kb()
    )
    await callback.answer()

async def save_incident(callback: CallbackQuery, incident_type: str, threat_level: int, description: str):
    telegram_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(select(Disciple).where(Disciple.telegram_id == telegram_id))
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