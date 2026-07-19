# keyboards/heresy_kb.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_dasha_report_kb() -> InlineKeyboardMarkup:
    """Клавиатура репорта об инциденте с Дашкой."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👁️ Видел Дашку", callback_data="dasha_sighting"),
            InlineKeyboardButton(text="💨 Атака Семёна", callback_data="semen_attack")
        ],
        [
            InlineKeyboardButton(text="💡 Мигание фонаря", callback_data="light_flicker"),
            InlineKeyboardButton(text="🆘 Крупный инцидент", callback_data="major_incident")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
        ]
    ])


def get_semen_battle_kb() -> InlineKeyboardMarkup:
    """Клавиатура боя с Семёном."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="😤 Задержать дыхание!", callback_data="hold_breath"),
            InlineKeyboardButton(text="☝️ Сила Пальца!", callback_data="finger_attack")
        ],
        [
            InlineKeyboardButton(text="🏃 Бежать!", callback_data="run_away")
        ]
    ])