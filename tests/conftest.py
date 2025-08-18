"""Pytest configuration for Agent Spy tests."""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import get_settings
from src.models.base import Base


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "database: mark test to run with database integration")
    config.addinivalue_line("markers", "sqlite: mark test to run with SQLite database")
    config.addinivalue_line("markers", "postgresql: mark test to run with PostgreSQL database")

    # Set testing environment variable
    os.environ["TESTING"] = "true"


def pytest_unconfigure(config):
    """Clean up after pytest."""
    # Remove testing environment variable
    os.environ.pop("TESTING", None)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def database_type() -> str:
    """Get the database type for testing."""
    return os.getenv("TEST_DATABASE_TYPE", "sqlite")


@pytest.fixture(scope="session")
def database_url(database_type: str) -> str:
    """Get the database URL for testing."""
    if database_type == "postgresql":
        # Use test PostgreSQL database
        return os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db")
    else:
        # Use in-memory SQLite for testing
        return "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def test_engine(database_url: str):
    """Create a test database engine."""
    engine = create_async_engine(
        database_url,
        echo=False,
        poolclass=None if database_url.startswith("sqlite") else None,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session_maker(test_engine) -> async_sessionmaker[AsyncSession]:
    """Create a test session maker."""
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture
async def test_session(test_session_maker) -> AsyncGenerator[AsyncSession]:
    """Create a test database session."""
    async with test_session_maker() as session:
        yield session
        # Clean up any data created during the test
        await session.rollback()
        # Clear the session to ensure no cached objects remain
        session.expunge_all()


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = get_settings()
    # Override settings for testing
    settings.database_type = "sqlite"
    settings.database_url = "sqlite+aiosqlite:///:memory:"
    settings.database_echo = False
    return settings


@pytest.fixture
def sqlite_settings():
    """Create SQLite-specific settings for testing."""
    with patch.dict(
        os.environ,
        {"DATABASE_TYPE": "sqlite", "DATABASE_URL": "sqlite+aiosqlite:///:memory:", "DATABASE_ECHO": "false"},
        clear=False,
    ):
        get_settings.cache_clear()
        settings = get_settings()
        yield settings
        get_settings.cache_clear()


@pytest.fixture
def postgresql_settings():
    """Create PostgreSQL-specific settings for testing."""
    with patch.dict(
        os.environ,
        {
            "DATABASE_TYPE": "postgresql",
            "DATABASE_HOST": "localhost",
            "DATABASE_PORT": "5432",
            "DATABASE_NAME": "test_db",
            "DATABASE_USER": "test_user",
            "DATABASE_PASSWORD": "test_pass",
            "DATABASE_SSL_MODE": "disable",
            "DATABASE_ECHO": "false",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        settings = get_settings()
        yield settings
        get_settings.cache_clear()


# Database-specific test markers
@pytest.mark.database
@pytest.mark.sqlite
def test_sqlite_marker():
    """Test marker for SQLite tests."""
    pass


@pytest.mark.database
@pytest.mark.postgresql
def test_postgresql_marker():
    """Test marker for PostgreSQL tests."""
    pass
