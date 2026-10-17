"""Database Connection and Session Management."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from backend.app.core.config import get_settings
from backend.app.core.logging import logger

settings = get_settings()

db_url = settings.DATABASE_URL

from sqlalchemy import event
from sqlalchemy.pool import NullPool

# Configure engine arguments based on driver
engine_kwargs = {"echo": False}
if "sqlite" in db_url:
    engine_kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30}
    engine_kwargs["poolclass"] = NullPool
else:
    # PostgreSQL pool settings
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_async_engine(db_url, **engine_kwargs)

if "sqlite" in db_url:
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session rollback due to exception: {e}")
            raise
        finally:
            await session.close()


async def init_db():
    """Initializes tables and seeds default user for local development / testing."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized successfully.")

    # Auto-seed default user if none exists
    try:
        from backend.app.models.user import User
        from backend.app.core.security import get_password_hash
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            res = await session.execute(select(User).limit(1))
            if not res.scalars().first():
                demo_user = User(
                    email="meens@example.com",
                    hashed_password=get_password_hash("password123"),
                    full_name="Meens",
                    is_active=True,
                )
                session.add(demo_user)
                await session.commit()
                logger.info("Auto-seeded default user: meens@example.com / password123")
    except Exception as e:
        logger.warning(f"Default user seeding skipped or failed: {e}")
