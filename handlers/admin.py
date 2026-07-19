# handlers/admin.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, update
from database.base import async_session
from database.models import Disciple, Ban
from keyboards.admin_kb import admin_panel_kb, admin_manage_admins_kb, back_to_admin_kb
from keyboards.lore_kb import get_main_menu_kb

router = Router()

class AdminStates(StatesGroup):
    waiting_for_user_id_ban = State()
    waiting_for_ban_reason = State()
    waiting_for_user_id_unban = State()
    waiting_for_add_admin_id = State()
    waiting_for_remove_admin_id = State()
    waiting_for_stats_user_id = State()

# Проверка админа через data["disciple"] (теперь в middleware)
def is_admin_check(disciple: Disciple | None) -> bool:
    return disciple is not None and disciple.is_admin

# Главное админ-меню
@router.message(Command("admin"))
async def admin_command(message: Message, disciple: Disciple = None):
    if not is_admin_check(disciple):
        await message.answer("⛔ Недостаточно прав.")
        return
    await message.answer("👑 *Админ-панель Магистра*", parse_mode="Markdown", reply_markup=admin_panel_kb())

@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery, disciple: Disciple = None):
    if not is_admin_check(disciple):
        await callback.answer("Нет прав", show_alert=True)
        return
    await callback.message.edit_text("👑 *Админ-панель Магистра*", parse_mode="Markdown", reply_markup=admin_panel_kb())

# Статистика всех
@router.callback_query(F.data == "admin_stats_all")
async def admin_stats_all(callback: CallbackQuery, disciple: Disciple = None):
    if not is_admin_check(disciple): return await callback.answer("Нет прав")
    async with async_session() as session:
        result = await session.execute(select(Disciple).order_by(Disciple.finger_power.desc()))
        all_d = result.scalars().all()
    if not all_d:
        await callback.message.edit_text("Нет учеников.", reply_markup=back_to_admin_kb())
        return
    text = "📊 *Все ученики:*\n"
    for d in all_d:
        text += f"• {d.nickname or d.full_name} (ID {d.telegram_id}) — {d.rank} | Сила: {d.finger_power:.1f}\n"
        text += f"  Тренировок: {d.total_workouts} | Инцидентов: {d.dasha_incidents_reported}\n"
        if d.is_admin: text += "  👑 Админ\n"
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=back_to_admin_kb())
    except:
        await callback.message.edit_text("Слишком длинный список.", reply_markup=back_to_admin_kb())
    await callback.answer()

# Статистика конкретного
@router.callback_query(F.data == "admin_stats_user")
async def admin_stats_user_prompt(callback: CallbackQuery, state: FSMContext, disciple: Disciple = None):
    if not is_admin_check(disciple): return await callback.answer("Нет прав")
    await state.set_state(AdminStates.waiting_for_stats_user_id)
    await callback.message.edit_text("Введите Telegram ID ученика:", reply_markup=back_to_admin_kb())
    await callback.answer()

@router.message(AdminStates.waiting_for_stats_user_id)
async def admin_stats_user_show(message: Message, state: FSMContext, disciple: Disciple = None):
    if not is_admin_check(disciple): return
    try:
        uid = int(message.text.strip())
    except:
        await message.answer("Некорректный ID.")
        return
    async with async_session() as session:
        result = await session.execute(select(Disciple).where(Disciple.telegram_id == uid))
        user = result.scalar_one_or_none()
    if not user:
        await message.answer("Ученик не найден.", reply_markup=back_to_admin_kb())
    else:
        text = (
            f"👤 *{user.nickname or user.full_name}* (ID {user.telegram_id})\n"
            f"Ранг: {user.rank} | Сила: {user.finger_power:.2f}\n"
            f"Тренировок: {user.total_workouts} | Поднято: {user.total_weight_lifted:.1f} кг\n"
            f"Инцидентов: {user.dasha_incidents_reported}\n"
            f"Боёв с Семёном: {user.semen_battles_won}W / {user.semen_battles_lost}L\n"
            f"Админ: {'Да' if user.is_admin else 'Нет'}\n"
            f"Смена ника: {'доступна' if user.can_change_nickname else 'использована'}"
        )
        await message.answer(text, parse_mode="Markdown", reply_markup=back_to_admin_kb())
    await state.clear()

# Бан
@router.callback_query(F.data == "admin_ban_user")
async def admin_ban_prompt(callback: CallbackQuery, state: FSMContext, disciple: Disciple = None):
    if not is_admin_check(disciple): return await callback.answer("Нет прав")
    await state.set_state(AdminStates.waiting_for_user_id_ban)
    await callback.message.edit_text("Введите Telegram ID для бана:", reply_markup=back_to_admin_kb())
    await callback.answer()

@router.message(AdminStates.waiting_for_user_id_ban)
async def admin_ban_get_id(message: Message, state: FSMContext, disciple: Disciple = None):
    if not is_admin_check(disciple): return
    try:
        uid = int(message.text.strip())
    except:
        await message.answer("Некорректный ID.")
        return
    await state.update_data(ban_user_id=uid)
    await state.set_state(AdminStates.waiting_for_ban_reason)
    await message.answer("Введите причину бана:")

@router.message(AdminStates.waiting_for_ban_reason)
async def admin_ban_execute(message: Message, state: FSMContext, disciple: Disciple = None):
    if not is_admin_check(disciple): return
    reason = message.text.strip()
    data = await state.get_data()
    user_id = data.get("ban_user_id")
    if not user_id:
        await state.clear()
        await message.answer("Ошибка. Начните заново.")
        return
    async with async_session() as session:
        result = await session.execute(select(Disciple).where(Disciple.telegram_id == user_id))
        target = result.scalar_one_or_none()
        if not target:
            await message.answer("Ученик не найден.")
        else:
            # Проверяем, нет ли активного бана
            existing = await session.execute(
                select(Ban).where(Ban.disciple_id == target.id, Ban.is_active == True)
            )
            if existing.scalar_one_or_none():
                await message.answer("У этого ученика уже активный бан.")
            else:
                ban = Ban(disciple_id=target.id, banned_by=disciple.telegram_id, reason=reason)
                session.add(ban)
                await session.commit()
                await message.answer(f"🚫 Ученик {target.nickname or target.full_name} забанен.\nПричина: {reason}")
    await state.clear()
    await message.answer("Возвращаемся.", reply_markup=admin_panel_kb())

# Разбан
@router.callback_query(F.data == "admin_unban_user")
async def admin_unban_prompt(callback: CallbackQuery, state: FSMContext, disciple: Disciple = None):
    if not is_admin_check(disciple): return await callback.answer("Нет прав")
    await state.set_state(AdminStates.waiting_for_user_id_unban)
    await callback.message.edit_text("Введите Telegram ID для разбана:", reply_markup=back_to_admin_kb())
    await callback.answer()

@router.message(AdminStates.waiting_for_user_id_unban)
async def admin_unban_execute(message: Message, state: FSMContext, disciple: Disciple = None):
    if not is_admin_check(disciple): return
    try:
        uid = int(message.text.strip())
    except:
        await message.answer("Некорректный ID.")
        return
    async with async_session() as session:
        result = await session.execute(select(Disciple).where(Disciple.telegram_id == uid))
        target = result.scalar_one_or_none()
        if not target:
            await message.answer("Ученик не найден.")
        else:
            ban_result = await session.execute(
                select(Ban).where(Ban.disciple_id == target.id, Ban.is_active == True)
            )
            ban = ban_result.scalar_one_or_none()
            if not ban:
                await message.answer("Активных банов нет.")
            else:
                ban.is_active = False
                await session.commit()
                await message.answer(f"✅ Ученик {target.nickname or target.full_name} разбанен.")
    await state.clear()
    await message.answer("Возвращаемся.", reply_markup=admin_panel_kb())

# Управление админами
@router.callback_query(F.data == "admin_manage_admins")
async def admin_manage_admins_menu(callback: CallbackQuery, disciple: Disciple = None):
    if not is_admin_check(disciple): return await callback.answer("Нет прав")
    await callback.message.edit_text("👑 *Управление админами*", parse_mode="Markdown", reply_markup=admin_manage_admins_kb())

@router.callback_query(F.data == "admin_list_admins")
async def list_admins(callback: CallbackQuery, disciple: Disciple = None):
    if not is_admin_check(disciple): return
    async with async_session() as session:
        result = await session.execute(select(Disciple).where(Disciple.is_admin == True))
        admins = result.scalars().all()
    if not admins:
        await callback.message.edit_text("Нет админов.", reply_markup=admin_manage_admins_kb())
    else:
        text = "👑 *Админы:*\n" + "\n".join(f"• {a.nickname or a.full_name} (ID {a.telegram_id})" for a in admins)
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=admin_manage_admins_kb())
    await callback.answer()

@router.callback_query(F.data == "admin_add_admin")
async def admin_add_prompt(callback: CallbackQuery, state: FSMContext, disciple: Disciple = None):
    if not is_admin_check(disciple): return
    await state.set_state(AdminStates.waiting_for_add_admin_id)
    await callback.message.edit_text("Введите Telegram ID нового админа:", reply_markup=back_to_admin_kb())
    await callback.answer()

@router.message(AdminStates.waiting_for_add_admin_id)
async def admin_add_execute(message: Message, state: FSMContext, disciple: Disciple = None):
    if not is_admin_check(disciple): return
    try:
        uid = int(message.text.strip())
    except:
        await message.answer("Некорректный ID.")
        return
    async with async_session() as session:
        result = await session.execute(select(Disciple).where(Disciple.telegram_id == uid))
        target = result.scalar_one_or_none()
        if not target:
            await message.answer("Ученик не найден. Сначала он должен зарегистрироваться через /start.")
        else:
            target.is_admin = True
            await session.commit()
            await message.answer(f"👑 {target.nickname or target.full_name} теперь админ.")
    await state.clear()
    await message.answer("Готово.", reply_markup=admin_panel_kb())

@router.callback_query(F.data == "admin_remove_admin")
async def admin_remove_prompt(callback: CallbackQuery, state: FSMContext, disciple: Disciple = None):
    if not is_admin_check(disciple): return
    await state.set_state(AdminStates.waiting_for_remove_admin_id)
    await callback.message.edit_text("Введите Telegram ID админа для снятия:", reply_markup=back_to_admin_kb())
    await callback.answer()

@router.message(AdminStates.waiting_for_remove_admin_id)
async def admin_remove_execute(message: Message, state: FSMContext, disciple: Disciple = None):
    if not is_admin_check(disciple): return
    try:
        uid = int(message.text.strip())
    except:
        await message.answer("Некорректный ID.")
        return
    async with async_session() as session:
        result = await session.execute(select(Disciple).where(Disciple.telegram_id == uid))
        target = result.scalar_one_or_none()
        if not target or not target.is_admin:
            await message.answer("Этот пользователь не админ.")
        else:
            # Не даём снять самого себя? Оставим как есть, но предупредим.
            if target.telegram_id == disciple.telegram_id:
                await message.answer("Нельзя снять себя.")
                return
            target.is_admin = False
            await session.commit()
            await message.answer(f"👑 {target.nickname or target.full_name} больше не админ.")
    await state.clear()
    await message.answer("Готово.", reply_markup=admin_panel_kb())