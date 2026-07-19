# database/base.py

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config import settings

def _make_async_url(url: str) -> str:
    """Превращает postgresql:// в postgresql+psycopg_async://"""
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg_async://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg_async://", 1)
    return url

async_db_url = _make_async_url(settings.DATABASE_URL)

engine = create_async_engine(
    async_db_url,
    echo=False,
    pool_size=5,
    max_overflow=5,
    pool_recycle=600,           # рецикл каждые 10 минут
    pool_pre_ping=True,         # пинг перед использованием
    connect_args={
        # TCP keepalive (теперь работает через psycopg)
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
        # остальное
        "statement_cache_size": 0,
        "application_name": "magister_bot",
        "options": "-c statement_timeout=60000",  # таймаут запроса 60 сек
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
    from database.models import Disciple
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("ALTER TABLE disciples ADD COLUMN IF NOT EXISTS nickname VARCHAR(64)"))
        await conn.execute(text("ALTER TABLE disciples ADD COLUMN IF NOT EXISTS can_change_nickname BOOLEAN DEFAULT TRUE"))
        await conn.execute(text("ALTER TABLE disciples ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE"))
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