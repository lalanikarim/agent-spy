"""Database connection and session management."""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from src.core.config import get_settings
from src.core.logging import get_logger
from src.models.base import Base

logger = get_logger(__name__)

# Global variables for engine and session maker
engine = None
async_session_maker = None


async def init_database() -> None:
    """Initialize the database connection and create tables."""
    global engine, async_session_maker

    settings = get_settings()
    database_url = settings.get_database_url()
    logger.info(f"Initializing database connection: {database_url}")

    # Configure engine based on database type
    if settings.database_type == "sqlite":
        # SQLite-specific configuration
        engine = create_async_engine(
            database_url,
            echo=settings.database_echo,
            poolclass=StaticPool,
            connect_args={
                "check_same_thread": False,
            },
        )
    elif settings.database_type == "postgresql":
        # PostgreSQL-specific configuration
        connect_args = {}

        # Add SSL configuration if specified
        if settings.database_ssl_mode != "disable":
            connect_args["ssl"] = True

        engine = create_async_engine(
            database_url,
            echo=settings.database_echo,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_connections - settings.database_pool_size,
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,  # Recycle connections every hour
            connect_args=connect_args,
        )
    else:
        # Fallback for other databases
        engine = create_async_engine(
            database_url,
            echo=settings.database_echo,
            pool_size=settings.database_pool_size,
            max_overflow=20,
        )

    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create all tables with retry logic
    logger.info("Creating database tables...")
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialization complete")
            break
        except OperationalError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database connection failed (attempt {attempt + 1}/{max_retries}): {e}")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"Failed to initialize database after {max_retries} attempts: {e}")
                raise


async def close_database() -> None:
    """Close the database connection."""
    global engine

    if engine:
        logger.info("Closing database connection...")
        await engine.dispose()
        logger.info("Database connection closed")


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """
    Get a database session.

    This is an async context manager that provides a database session
    and handles cleanup automatically.

    Usage:
        async with get_db_session() as session:
            # Use session here
            result = await session.execute(select(Run))
    """
    if not async_session_maker:
        raise RuntimeError("Database not initialized. Call init_database() first.")

    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession]:
    """
    Dependency function for FastAPI to get database session.

    This is used as a FastAPI dependency to inject database sessions
    into route handlers.

    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            # Use db session here
    """
    async with get_db_session() as session:
        yield session
