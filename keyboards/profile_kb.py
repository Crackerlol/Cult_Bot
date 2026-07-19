# keyboards/profile_kb.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.lore_kb import get_main_menu_kb

def get_profile_keyboard(disciple) -> InlineKeyboardMarkup:
    buttons = []
    if disciple.can_change_nickname:
        buttons.append([InlineKeyboardButton(text="🔄 Сменить ник", callback_data="change_nickname")])
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)