"""Unit tests for PostgreSQL configuration."""

import os

import pytest

from src.core.config import get_settings


class TestPostgreSQLConfiguration:
    """Test PostgreSQL configuration functionality."""

    def test_default_database_type(self):
        """Test that default database type is sqlite."""
        settings = get_settings()
        assert settings.database_type == "sqlite"

    def test_database_type_validation(self):
        """Test database type validation."""
        # Test valid database types by creating new settings instances
        # This tests the actual validation logic

        # Test case insensitivity through environment variables
        os.environ["DATABASE_TYPE"] = "SQLITE"
        try:
            get_settings.cache_clear()
            settings = get_settings()
            assert settings.database_type == "sqlite"
        finally:
            os.environ.pop("DATABASE_TYPE", None)
            get_settings.cache_clear()

        os.environ["DATABASE_TYPE"] = "POSTGRESQL"
        try:
            get_settings.cache_clear()
            settings = get_settings()
            assert settings.database_type == "postgresql"
        finally:
            os.environ.pop("DATABASE_TYPE", None)
            get_settings.cache_clear()

    def test_invalid_database_type(self):
        """Test that invalid database type raises error."""
        with pytest.raises(ValueError, match="Database type must be one of"):
            # This would normally be set via environment variable
            # For testing, we'll create a new settings instance
            class TestSettings(get_settings().__class__):
                database_type: str = "invalid"

            TestSettings()

    def test_postgresql_url_construction(self):
        """Test PostgreSQL URL construction from components."""
        settings = get_settings()

        # Set PostgreSQL configuration
        settings.database_type = "postgresql"
        settings.database_host = "localhost"
        settings.database_port = 5432
        settings.database_name = "test_db"
        settings.database_user = "test_user"
        settings.database_password = "test_pass"

        # Test URL construction
        url = settings.get_database_url()
        expected = "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db"
        assert url == expected

    def test_postgresql_url_construction_no_password(self):
        """Test PostgreSQL URL construction without password."""
        settings = get_settings()

        # Set PostgreSQL configuration without password
        settings.database_type = "postgresql"
        settings.database_host = "localhost"
        settings.database_port = 5432
        settings.database_name = "test_db"
        settings.database_user = "test_user"
        settings.database_password = ""

        # Test URL construction
        url = settings.get_database_url()
        expected = "postgresql+asyncpg://test_user@localhost:5432/test_db"
        assert url == expected

    def test_ssl_mode_validation(self):
        """Test SSL mode validation."""
        # Test valid SSL modes through environment variables
        valid_modes = ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]
        for mode in valid_modes:
            os.environ["DATABASE_SSL_MODE"] = mode
            try:
                get_settings.cache_clear()
                settings = get_settings()
                assert settings.database_ssl_mode == mode
            finally:
                os.environ.pop("DATABASE_SSL_MODE", None)
                get_settings.cache_clear()

        # Test case insensitivity
        os.environ["DATABASE_SSL_MODE"] = "PREFER"
        try:
            get_settings.cache_clear()
            settings = get_settings()
            assert settings.database_ssl_mode == "prefer"
        finally:
            os.environ.pop("DATABASE_SSL_MODE", None)
            get_settings.cache_clear()

    def test_invalid_ssl_mode(self):
        """Test that invalid SSL mode raises error."""
        with pytest.raises(ValueError, match="SSL mode must be one of"):
            class TestSettings(get_settings().__class__):
                database_ssl_mode: str = "invalid"

            TestSettings()

    def test_direct_url_override(self):
        """Test that direct DATABASE_URL overrides component construction."""
        settings = get_settings()

        # Set a direct URL
        direct_url = "postgresql+asyncpg://custom_user:custom_pass@custom_host:5433/custom_db"
        settings.database_url = direct_url

        # Set PostgreSQL components (should be ignored)
        settings.database_type = "postgresql"
        settings.database_host = "localhost"
        settings.database_port = 5432
        settings.database_name = "test_db"
        settings.database_user = "test_user"
        settings.database_password = "test_pass"

        # Should return the direct URL
        url = settings.get_database_url()
        assert url == direct_url

    def test_sqlite_default_url(self):
        """Test that SQLite returns default URL when no direct URL is set."""
        settings = get_settings()

        # Reset to default SQLite configuration
        settings.database_type = "sqlite"
        settings.database_url = "sqlite+aiosqlite:///./agentspy.db"

        url = settings.get_database_url()
        assert url == "sqlite+aiosqlite:///./agentspy.db"

    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        # Set environment variables
        os.environ["DATABASE_TYPE"] = "postgresql"
        os.environ["DATABASE_HOST"] = "env_host"
        os.environ["DATABASE_PORT"] = "5433"
        os.environ["DATABASE_NAME"] = "env_db"
        os.environ["DATABASE_USER"] = "env_user"
        os.environ["DATABASE_PASSWORD"] = "env_pass"

        try:
            # Clear the settings cache to force reload
            get_settings.cache_clear()

            # Create new settings instance to pick up environment variables
            settings = get_settings()

            # Verify environment variables are used
            assert settings.database_type == "postgresql"
            assert settings.database_host == "env_host"
            assert settings.database_port == 5433
            assert settings.database_name == "env_db"
            assert settings.database_user == "env_user"
            assert settings.database_password == "env_pass"

            # Test URL construction with environment variables
            url = settings.get_database_url()
            expected = "postgresql+asyncpg://env_user:env_pass@env_host:5433/env_db"
            assert url == expected

        finally:
            # Clean up environment variables
            for var in ["DATABASE_TYPE", "DATABASE_HOST", "DATABASE_PORT",
                       "DATABASE_NAME", "DATABASE_USER", "DATABASE_PASSWORD"]:
                os.environ.pop(var, None)
            # Restore cache
            get_settings.cache_clear()
