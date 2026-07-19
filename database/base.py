# database/base.py

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config import settings

def _make_async_url(url: str) -> str:
    """Превращает синхронный postgresql:// в асинхронный postgresql+asyncpg://"""
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url

# Получаем готовый URL с +asyncpg
async_db_url = _make_async_url(settings.DATABASE_URL)

# Движок PostgreSQL (asyncpg) с проверкой соединения перед использованием
engine = create_async_engine(
    async_db_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # <-- ВОТ ОНА, МАГИЯ: проверяет, живо ли соединение
)

# Фабрика сессий
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    """Генератор сессий."""
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
    """Создаёт все таблицы при старте."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)