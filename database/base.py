# database/base.py

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config import settings

def _make_async_url(url: str) -> str:
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url

async_db_url = _make_async_url(settings.DATABASE_URL)

engine = create_async_engine(
    async_db_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True,
    connect_args={
        "ssl": False,
        "statement_cache_size": 0,
        "server_settings": {"application_name": "magister_bot"},
        "timeout": 60,
        "command_timeout": 60,
    },
    pool_use_lifo=True,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
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
    async with engine.begin() as conn:
        # Создаём таблицы, если их ещё нет
        await conn.run_sync(Base.metadata.create_all)

        # Добавляем недостающие колонки (для обновления существующих таблиц)
        await conn.execute(text(
            "ALTER TABLE disciples ADD COLUMN IF NOT EXISTS nickname VARCHAR(64)"
        ))
        await conn.execute(text(
            "ALTER TABLE disciples ADD COLUMN IF NOT EXISTS can_change_nickname BOOLEAN DEFAULT TRUE"
        ))