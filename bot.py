# bot.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import settings
from database.base import init_db
from handlers import lore, training, heresy, profile, admin, ranks, lore_stories
from middlewares.dasha_shield import DashaShieldMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def main():
    logger.info("☝️ Магистр пробуждается...")
    await init_db()
    logger.info("✅ База готова")

    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Только щит от Дашки (для всех сообщений)
    dp.message.middleware(DashaShieldMiddleware())

    # Роутеры
    dp.include_router(profile.router)
    dp.include_router(admin.router)
    dp.include_router(ranks.router)
    dp.include_router(lore.router)
    dp.include_router(lore_stories.router)
    dp.include_router(training.router)
    dp.include_router(heresy.router)

    logger.info("Роутеры зарегистрированы")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Магистр уходит в тень.")
    except Exception as e:
        logger.error(f"Ошибка: {e}")