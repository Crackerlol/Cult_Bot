# keyboards/admin_kb.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_panel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика всех", callback_data="admin_stats_all")],
        [InlineKeyboardButton(text="🔍 Статистика ученика", callback_data="admin_stats_user")],
        [InlineKeyboardButton(text="🚫 Забанить", callback_data="admin_ban_user")],
        [InlineKeyboardButton(text="✅ Разбанить", callback_data="admin_unban_user")],
        [InlineKeyboardButton(text="👑 Админы", callback_data="admin_manage_admins")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])

def admin_manage_admins_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить админа", callback_data="admin_add_admin")],
        [InlineKeyboardButton(text="➖ Удалить админа", callback_data="admin_remove_admin")],
        [InlineKeyboardButton(text="📋 Список админов", callback_data="admin_list_admins")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])

def back_to_admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад в админку", callback_data="admin_back")]
    ])