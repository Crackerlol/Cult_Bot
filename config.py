# config.py

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Настройки бота, благословлённые Магистром."""
    
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://magister:sila_palca_1488@localhost:5433/cult_bd")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Админы — ID кентов через запятую в .env
    ADMIN_IDS: list[int] = [
        int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
    ]
    
    # Вероятность что Магистр сам выдаст мудрость после тренировки
    MAGISTER_WISDOM_CHANCE: float = float(os.getenv("MAGISTER_WISDOM_CHANCE", "0.3"))
    
    # Уровень угрозы Дашки
    DASHA_THREAT_LEVEL: str = os.getenv("DASHA_THREAT_LEVEL", "medium")
    
    # Система рангов учеников
    RANKS: dict[int, str] = {
        0: "Новоприбывший",
        100: "Ученик",
        500: "Адепт",
        1000: "Послушник Пальца",
        5000: "Страж Остановки",
        10000: "Хранитель Времени",
        50000: "Десница Магистра",
    }
    
    DASHA_MINIONS: list[str] = ["Семён Вонючий", "Тёмный Хлюпик", "Еретик-недомытый"]

settings = Settings()