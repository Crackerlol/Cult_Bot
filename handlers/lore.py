# handlers/lore.py

import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from keyboards.lore_kb import get_lore_keyboard, get_back_to_magister_kb, get_main_menu_kb

router = Router()

# Священный катехизис Магистра Естествознания
WISDOMS = [
    "Я сотворил мир, пока ты спал. А теперь жми штангу.",
    "Указательный палец — не просто палец. Это ключ к остановке автобуса и времени. Понял, нет?",
    "Дашка — чернь. Семён — вонючка. Ты — ученик. Не перепутай.",
    "Когда гасишь свет — думай, кто гасит твой. Дашка рядом, только если ты слаб.",
    "Первая ученица предала меня. Но я обрёл пять новых. Судьба? Нет. Жим лёжа.",
    "Тряси указательным пальцем не для TikTok. Тряси для заморозки времени. Познай дзен.",
    "Семён моется раз в год. Ты тренируешься каждый день. Вопрос: кто опаснее?",
    "Я бомж, но я Магистр. В этом суть естествознания.",
    "Автобус не остановить силой мысли. Только силой пальца и духа.",
    "Дашка извратила мою веру. Не дай ей извратить твой подход. Жми до отказа.",
    "Пять учеников на остановке познали истину. А ты познал её в качалке. Разницы нет.",
    "Твоя ладошка способна на многое. Но сначала — разминка.",
    "Я создал этот мир из хлебных крошек и пота с тренировок. Уважай железо.",
    "Заморозка времени — это не фокус. Это дисциплина. И указательный палец.",
    "Семён — биологическое оружие. Но даже против него есть противогаз: сила духа.",
]

DASHA_THREATS = [
    "⚠️ Чувствую вонь Семёна в радиусе трёх кварталов. Дашка близко. Качай бицепс.",
    "⚠️ Фонарь у дома ученика мигнул. Это не электричество. Это чернь.",
    "⚠️ Дашка плетёт интриги. Семён не мылся со времён прошлого солнцестояния. Угроза: высокая.",
    "⚠️ Тёмная энергия сгущается у подъезда. Дашка направила Семёна в разведку. Будь готов.",
    "⚠️ Глаз Дашки следит за качалкой. Она знает кто сегодня пропустил тренировку.",
    "⚠️ Семён сменил носки? Невозможно. Но Дашка что-то замышляет. Бди.",
]


@router.message(Command("magister"))
async def magister_command(message: Message):
    """Призывает мудрость Магистра через кнопки."""
    wisdom = random.choice(WISDOMS)
    keyboard = get_lore_keyboard()
    await message.answer(
        f"🧙‍♂️ *Магистр Естествознания изрёк:* \n\n_{wisdom}_",
        parse_mode="Markdown",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "more_wisdom")
async def more_wisdom(callback: CallbackQuery):
    """Выдаёт ещё одну мудрость."""
    wisdom = random.choice(WISDOMS)
    keyboard = get_lore_keyboard()
    await callback.message.edit_text(
        f"🧙‍♂️ *Магистр Естествознания изрёк:* \n\n_{wisdom}_",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer("🧠 Магистр услышал тебя")


@router.callback_query(F.data == "check_dasha")
async def check_dasha(callback: CallbackQuery):
    """Проверка угрозы от Дашки."""
    threat = random.choice(DASHA_THREATS)
    keyboard = get_back_to_magister_kb()
    await callback.message.edit_text(
        f"🔮 *Разведка донесла:* \n\n{threat}",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer("⚠️ Дашка не дремлет")


@router.callback_query(F.data == "back_to_magister")
async def back_to_magister(callback: CallbackQuery):
    """Возврат к мудрости Магистра."""
    wisdom = random.choice(WISDOMS)
    keyboard = get_lore_keyboard()
    await callback.message.edit_text(
        f"🧙‍♂️ *Магистр Естествознания изрёк:* \n\n_{wisdom}_",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer("Ты снова у ног Магистра")


@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery):
    """Главное меню."""
    keyboard = get_main_menu_kb()
    await callback.message.edit_text(
        "🏛 *Культ Магистра Естествознания*\n\n"
        "Выбери действие, ученик:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer("Главное меню")


@router.message(Command("start"))
async def start_command(message: Message):
    """Приветствие нового ученика."""
    keyboard = get_main_menu_kb()
    await message.answer(
        "🏛 *Добро пожаловать в Культ Магистра Естествознания!*\n\n"
        "Я — ученик Магистра, посланный помогать новым адептам.\n\n"
        "Что желаешь, брат?\n"
        "• /magister — испросить мудрость Магистра\n"
        "• /training — записать тренировку\n"
        "• /report — доложить о происках Дашки\n"
        "• /stats — твоя статистика",
        parse_mode="Markdown",
        reply_markup=keyboard
    )