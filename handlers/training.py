# handlers/training.py
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from database.base import async_session
from database.models import Disciple, Training
from keyboards.training_kb import get_exercise_keyboard, get_training_complete_kb
from keyboards.lore_kb import get_main_menu_kb
from utils.finger_power import calculate_finger_power, get_rank, get_next_rank
from utils.disciple_utils import get_disciple, is_banned

router = Router()

class TrainingStates(StatesGroup):
    waiting_for_sets = State()
    waiting_for_reps = State()
    waiting_for_weight = State()

# --- Проверка доступа ---
async def check_access(user_id: int) -> Disciple | None:
    """Возвращает ученика, если он зарегистрирован и не забанен, иначе None."""
    disciple = await get_disciple(user_id)
    if not disciple:
        return None
    if not disciple.is_admin:
        ban = await is_banned(disciple)
        if ban:
            return None  # Забанен
    return disciple

# --- Начало тренировки ---
@router.callback_query(F.data == "start_training")
async def start_training(callback: CallbackQuery, state: FSMContext):
    disciple = await check_access(callback.from_user.id)
    if not disciple:
        await callback.message.edit_text("⛔ Ты не можешь тренироваться. Проверь /start и свой статус.", reply_markup=get_main_menu_kb())
        await callback.answer()
        return
    keyboard = get_exercise_keyboard()
    await callback.message.edit_text("💪 *Выбери упражнение, ученик:*", parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("exercise_"))
async def exercise_selected(callback: CallbackQuery, state: FSMContext):
    disciple = await check_access(callback.from_user.id)
    if not disciple:
        await callback.message.edit_text("⛔ Доступ запрещён.", reply_markup=get_main_menu_kb())
        await callback.answer()
        return
    exercise = callback.data.replace("exercise_", "")
    await state.update_data(exercise=exercise)
    await state.set_state(TrainingStates.waiting_for_sets)
    await callback.message.edit_text(
        f"🏋️ *Упражнение:* _{exercise}_\n\nСколько подходов сделал?\n_(Отправь число от 1 до 20)_",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(TrainingStates.waiting_for_sets)
async def sets_entered(message: Message, state: FSMContext):
    disciple = await check_access(message.from_user.id)
    if not disciple:
        await message.answer("⛔ Сначала /start.")
        return
    try:
        sets = int(message.text.strip())
        if sets < 1 or sets > 20:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Отправь число от 1 до 20, ученик.")
        return
    await state.update_data(sets=sets)
    await state.set_state(TrainingStates.waiting_for_reps)
    await message.answer(f"🔢 Подходов: *{sets}*\n\nСколько повторений в подходе?\n_(Отправь число от 1 до 50)_", parse_mode="Markdown")

@router.message(TrainingStates.waiting_for_reps)
async def reps_entered(message: Message, state: FSMContext):
    try:
        reps = int(message.text.strip())
        if reps < 1 or reps > 50:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Отправь число от 1 до 50, ученик.")
        return
    await state.update_data(reps=reps)
    await state.set_state(TrainingStates.waiting_for_weight)
    await message.answer(f"🔢 Повторений: *{reps}*\n\nКакой рабочий вес в килограммах?\n_(Отправь число от 0 до 500, можно с десятыми)_", parse_mode="Markdown")

@router.message(TrainingStates.waiting_for_weight)
async def weight_entered(message: Message, state: FSMContext):
    disciple = await check_access(message.from_user.id)
    if not disciple:
        await message.answer("⛔ Доступ запрещён.")
        return
    try:
        weight = float(message.text.strip().replace(",", "."))
        if weight < 0 or weight > 500:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Отправь число от 0 до 500, ученик.")
        return

    data = await state.get_data()
    exercise = data["exercise"]
    sets = data["sets"]
    reps = data["reps"]

    finger_power_earned = calculate_finger_power(sets, reps, weight, exercise)

    # Используем disciple из check_access, он уже свежий
    # Но чтобы учесть возможный дебафф, подгрузим из БД ещё раз внутри сессии
    async with async_session() as session:
        db_disciple = await session.get(Disciple, disciple.id)
        if not db_disciple:
            await message.answer("Ошибка данных.")
            return

        debuff_multiplier = 1.0
        if db_disciple.has_semen_debuff and db_disciple.semen_debuff_until:
            if datetime.utcnow() < db_disciple.semen_debuff_until:
                debuff_multiplier = 0.9
                await message.answer("💨 *Вонь Семёна всё ещё с тобой...* Эффективность снижена на 10%", parse_mode="Markdown")
            else:
                db_disciple.has_semen_debuff = False
                db_disciple.semen_debuff_until = None

        final_power = finger_power_earned * debuff_multiplier

        training = Training(
            disciple_id=db_disciple.id,
            exercise=exercise,
            sets=sets,
            reps=reps,
            weight=weight,
            finger_power_earned=final_power,
        )
        session.add(training)

        db_disciple.finger_power += final_power
        db_disciple.total_workouts += 1
        db_disciple.total_approaches += sets
        db_disciple.total_weight_lifted += weight * sets * reps
        db_disciple.last_training = datetime.utcnow()

        old_rank = db_disciple.rank
        new_rank = get_rank(db_disciple.finger_power)
        db_disciple.rank = new_rank

        await session.commit()

    await state.clear()

    next_rank, remaining = get_next_rank(db_disciple.finger_power)
    response = (
        f"✅ *Тренировка записана!*\n\n"
        f"🏋️ Упражнение: _{exercise}_\n"
        f"🔢 Подходов: {sets} | Повторений: {reps}\n"
        f"🏋️ Вес: {weight} кг\n\n"
        f"☝️ Сила пальца: *+{final_power}*\n"
        f"📊 Всего силы: *{db_disciple.finger_power:.2f}*\n"
        f"🎖 Ранг: *{new_rank}*"
    )
    if old_rank != new_rank:
        response += f"\n\n🎉 *ПОВЫШЕНИЕ!* Ты достиг ранга «{new_rank}»!"
    if remaining > 0:
        response += f"\n📈 До ранга «{next_rank}» осталось: *{remaining:.2f}* силы."

    keyboard = get_training_complete_kb()
    await message.answer(response, parse_mode="Markdown", reply_markup=keyboard)

@router.message(Command("training"))
async def training_command(message: Message, state: FSMContext):
    disciple = await check_access(message.from_user.id)
    if not disciple:
        await message.answer("⛔ Сначала /start.")
        return
    keyboard = get_exercise_keyboard()
    await message.answer("💪 *Выбери упражнение, ученик:*", parse_mode="Markdown", reply_markup=keyboard)

@router.callback_query(F.data == "my_stats")
async def my_stats(callback: CallbackQuery):
    disciple = await check_access(callback.from_user.id)
    if not disciple:
        await callback.message.edit_text("⛔ Нет доступа.", reply_markup=get_main_menu_kb())
        await callback.answer()
        return

    # Загружаем свежие данные
    async with async_session() as session:
        db_disciple = await session.get(Disciple, disciple.id)
        if not db_disciple:
            await callback.answer("Ошибка.")
            return

    next_rank, remaining = get_next_rank(db_disciple.finger_power)
    debuff_text = ""
    if db_disciple.has_semen_debuff:
        debuff_text = "\n💨 *Активен дебафф: Вонь Семёна (-10% к тренировкам)*"

    stats = (
        f"📊 *Твоя статистика, ученик:*\n\n"
        f"🎖 Ранг: *{db_disciple.rank}*\n"
        f"☝️ Сила пальца: *{db_disciple.finger_power:.2f}*\n"
        f"💪 Тренировок: *{db_disciple.total_workouts}*\n"
        f"🔢 Всего подходов: *{db_disciple.total_approaches}*\n"
        f"🏋️ Поднято веса: *{db_disciple.total_weight_lifted:.1f} кг*\n\n"
        f"⚠️ Инцидентов с Дашкой: *{db_disciple.dasha_incidents_reported}*\n"
        f"💨 Боёв с Семёном: *{db_disciple.semen_battles_won}* побед / *{db_disciple.semen_battles_lost}* поражений\n"
        f"{debuff_text}\n"
        f"📈 До ранга «{next_rank}»: *{remaining:.2f}* силы"
    )

    keyboard = get_main_menu_kb()
    try:
        await callback.message.edit_text(stats, parse_mode="Markdown", reply_markup=keyboard)
    except:
        await callback.answer("Статистика не изменилась", show_alert=True)
        return
    await callback.answer()