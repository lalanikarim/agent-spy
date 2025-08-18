"""Unit tests for PostgreSQL configuration."""

import os
from unittest.mock import patch

import pytest

from src.core.config import get_settings


class TestPostgreSQLConfiguration:
    """Test PostgreSQL configuration functionality."""

    def test_default_database_type_sqlite(self, sqlite_settings):
        """Test that default database type is sqlite when configured for SQLite."""
        assert sqlite_settings.database_type == "sqlite"

    def test_default_database_type_postgresql(self, postgresql_settings):
        """Test that database type is postgresql when configured for PostgreSQL."""
        assert postgresql_settings.database_type == "postgresql"

    def test_database_type_validation(self):
        """Test database type validation."""
        # Test valid database types by creating new settings instances
        # This tests the actual validation logic

        # Test case insensitivity through environment variables
        with patch.dict(os.environ, {"DATABASE_TYPE": "SQLITE"}, clear=False):
            get_settings.cache_clear()
            settings = get_settings()
            assert settings.database_type == "sqlite"

        with patch.dict(os.environ, {"DATABASE_TYPE": "POSTGRESQL"}, clear=False):
            get_settings.cache_clear()
            settings = get_settings()
            assert settings.database_type == "postgresql"

    def test_invalid_database_type(self):
        """Test that invalid database type raises error."""
        with (
            pytest.raises(ValueError, match="Database type must be one of"),
            patch.dict(os.environ, {"DATABASE_TYPE": "invalid"}, clear=False),
        ):
            get_settings.cache_clear()
            get_settings()

    def test_postgresql_url_construction(self, postgresql_settings):
        """Test PostgreSQL URL construction from components."""
        settings = postgresql_settings

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

    def test_postgresql_url_construction_no_password(self, postgresql_settings):
        """Test PostgreSQL URL construction without password."""
        settings = postgresql_settings

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
            with patch.dict(os.environ, {"DATABASE_SSL_MODE": mode}, clear=False):
                get_settings.cache_clear()
                settings = get_settings()
                assert settings.database_ssl_mode == mode

        # Test case insensitivity
        with patch.dict(os.environ, {"DATABASE_SSL_MODE": "PREFER"}, clear=False):
            get_settings.cache_clear()
            settings = get_settings()
            assert settings.database_ssl_mode == "prefer"

    def test_invalid_ssl_mode(self):
        """Test that invalid SSL mode raises error."""
        with (
            pytest.raises(ValueError, match="SSL mode must be one of"),
            patch.dict(os.environ, {"DATABASE_SSL_MODE": "invalid"}, clear=False),
        ):
            get_settings.cache_clear()
            get_settings()

    def test_direct_url_override(self, postgresql_settings):
        """Test that direct DATABASE_URL overrides component construction."""
        settings = postgresql_settings

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

    def test_sqlite_default_url(self, sqlite_settings):
        """Test that SQLite returns default URL when no direct URL is set."""
        settings = sqlite_settings

        # Reset to default SQLite configuration
        settings.database_type = "sqlite"
        settings.database_url = "sqlite+aiosqlite:///./agentspy.db"

        url = settings.get_database_url()
        assert url == "sqlite+aiosqlite:///./agentspy.db"

    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        # Set environment variables
        env_vars = {
            "DATABASE_TYPE": "postgresql",
            "DATABASE_HOST": "env_host",
            "DATABASE_PORT": "5433",
            "DATABASE_NAME": "env_db",
            "DATABASE_USER": "env_user",
            "DATABASE_PASSWORD": "env_pass",
        }

        with patch.dict(os.environ, env_vars, clear=False):
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
