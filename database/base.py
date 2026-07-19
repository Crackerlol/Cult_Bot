# database/base.py

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config import settings

# Движок PostgreSQL (asyncpg)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Поставь True если хочешь видеть SQL запросы
    pool_size=10,
    max_overflow=20,
)

# Фабрика сессий
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Базовый класс для моделей
class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    """Генератор сессий для внедрения зависимости."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Создаёт все таблицы. Вызывается при старте бота."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)