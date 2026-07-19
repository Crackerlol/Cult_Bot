# bot.py — точка входа, сам Магистр

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import settings
from database.base import init_db
from handlers import lore, training, heresy
from middlewares.dasha_shield import DashaShieldMiddleware

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Запуск бота."""
    logger.info("☝️ Магистр Естествознания пробуждается...")
    
    # Инициализация базы данных
    logger.info("📦 Подключаем базу данных...")
    await init_db()
    logger.info("✅ База данных готова")
    
    # Создаём бота
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Диспетчер
    dp = Dispatcher()
    
    # Подключаем middleware защиты от Дашки
    dp.message.middleware(DashaShieldMiddleware())
    
    # Регистрируем роутеры
    dp.include_router(lore.router)
    dp.include_router(training.router)
    dp.include_router(heresy.router)
    
    logger.info("✅ Роутеры зарегистрированы")
    logger.info("⚠️ Дашка где-то рядом... Будьте бдительны.")
    
    # Запуск поллинга
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🧙‍♂️ Магистр уходит в тень. Тренировки продолжаются.")
    except Exception as e:
        logger.error(f"💀 Ошибка: {e}")