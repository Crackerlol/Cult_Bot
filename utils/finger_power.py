# utils/finger_power.py

import random
from config import settings


def calculate_finger_power(sets: int, reps: int, weight: float, exercise: str) -> float:
    """
    Рассчитывает начисляемую силу указательного пальца за тренировку.
    Формула: (сеты * повторы * вес * коэффициент упражнения) / 100
    """
    # Коэффициенты для разных упражнений
    exercise_multipliers = {
        "жим лёжа": 1.5,
        "присед": 1.3,
        "становая тяга": 1.8,
        "подтягивания": 1.2,
        "отжимания": 1.0,
        "армейский жим": 1.4,
        "махи гирей": 1.1,
        "упражнение на палец": 2.0,  # Священное упражнение
    }
    
    multiplier = exercise_multipliers.get(exercise.lower(), 1.0)
    
    # Базовая формула
    base_power = (sets * reps * weight * multiplier) / 100
    
    # Случайный бонус от Магистра (0-10%)
    magister_blessing = random.uniform(0, 0.1) * base_power
    
    return round(base_power + magister_blessing, 2)


def get_rank(finger_power: float) -> str:
    """Возвращает ранг ученика в зависимости от силы пальца."""
    ranks = sorted(settings.RANKS.items(), key=lambda x: x[0])
    current_rank = "Новоприбывший"
    
    for threshold, rank_name in ranks:
        if finger_power >= threshold:
            current_rank = rank_name
        else:
            break
    
    return current_rank


def get_next_rank(finger_power: float) -> tuple[str, float]:
    """
    Возвращает следующий ранг и сколько осталось до него.
    Если ранг максимальный — возвращает (текущий_ранг, 0).
    """
    ranks = sorted(settings.RANKS.items(), key=lambda x: x[0])
    
    for i, (threshold, rank_name) in enumerate(ranks):
        if finger_power < threshold:
            remaining = threshold - finger_power
            return rank_name, remaining
    
    # Максимальный ранг
    max_rank = ranks[-1][1]
    return max_rank, 0.0