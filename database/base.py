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

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

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
    from database.models import Disciple  # локальный импорт, чтобы избежать циклов
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # добавляем колонки, если их нет
        await conn.execute(text("ALTER TABLE disciples ADD COLUMN IF NOT EXISTS nickname VARCHAR(64)"))
        await conn.execute(text("ALTER TABLE disciples ADD COLUMN IF NOT EXISTS can_change_nickname BOOLEAN DEFAULT TRUE"))
        await conn.execute(text("ALTER TABLE disciples ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE"))
        # таблица bans создаётся через create_all, но на всякий случай
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bans (
                id SERIAL PRIMARY KEY,
                disciple_id INTEGER REFERENCES disciples(id),
                banned_by INTEGER NOT NULL,
                reason TEXT,
                banned_at TIMESTAMP DEFAULT NOW(),
                is_active BOOLEAN DEFAULT TRUE
            )
        """))

    # Назначаем админов из config.ADMIN_IDS
    async with async_session() as session:
        from sqlalchemy import select
        for admin_id in settings.ADMIN_IDS:
            result = await session.execute(
                select(Disciple).where(Disciple.telegram_id == admin_id)
            )
            disciple = result.scalar_one_or_none()
            if disciple and not disciple.is_admin:
                disciple.is_admin = True
                await session.commit()