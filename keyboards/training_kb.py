# keyboards/training_kb.py

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_exercise_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора упражнения."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏋️ Жим лёжа", callback_data="exercise_жим лёжа"),
            InlineKeyboardButton(text="🦵 Присед", callback_data="exercise_присед")
        ],
        [
            InlineKeyboardButton(text="🔙 Становая тяга", callback_data="exercise_становая тяга"),
            InlineKeyboardButton(text="💪 Подтягивания", callback_data="exercise_подтягивания")
        ],
        [
            InlineKeyboardButton(text="🤲 Отжимания", callback_data="exercise_отжимания"),
            InlineKeyboardButton(text="🎯 Армейский жим", callback_data="exercise_армейский жим")
        ],
        [
            InlineKeyboardButton(text="☝️ Священный Палец", callback_data="exercise_упражнение на палец"),
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
        ]
    ])


def get_training_complete_kb() -> InlineKeyboardMarkup:
    """Клавиатура после завершения тренировки."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💪 Ещё тренировка", callback_data="start_training"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="my_stats")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ])