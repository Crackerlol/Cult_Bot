# keyboards/lore_kb.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_lore_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧠 Ещё мудрость", callback_data="more_wisdom"),
         InlineKeyboardButton(text="🔮 Проверить Дашку", callback_data="check_dasha")],
        [InlineKeyboardButton(text="💪 Тренировка", callback_data="start_training"),
         InlineKeyboardButton(text="📊 Мой прогресс", callback_data="my_stats")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="my_profile"),
         InlineKeyboardButton(text="👥 Ученики", callback_data="public_ranks")],
        [InlineKeyboardButton(text="📜 Истории Магистра", callback_data="magister_story")]
    ])

def get_back_to_magister_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Вернуться к Магистру", callback_data="back_to_magister"),
         InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])

def get_main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧙‍♂️ Магистр", callback_data="back_to_magister"),
         InlineKeyboardButton(text="💪 Тренировка", callback_data="start_training")],
        [InlineKeyboardButton(text="⚠️ Инцидент Дашки", callback_data="report_dasha"),
         InlineKeyboardButton(text="📊 Статистика", callback_data="my_stats")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="my_profile"),
         InlineKeyboardButton(text="👥 Ученики", callback_data="public_ranks")],
        [InlineKeyboardButton(text="📜 Истории Магистра", callback_data="magister_story")]
    ])