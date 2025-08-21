"""Configuration management for Agent Spy."""

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
        # Load .env file first, then allow environment variables to override
        env_file_encoding="utf-8",
    )

    # Application Settings
    app_name: str = "Agent Spy"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)",
    )

    # Server Settings
    host: str = Field(default="0.0.0.0", description="Server host")  # nosec B104
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=False, description="Auto-reload on code changes")

    # Database Settings
    database_url: str = Field(
        default="sqlite+aiosqlite:///./agentspy.db",
        description="Database connection URL",
    )
    database_type: str = Field(
        default="sqlite",
        description="Database type (sqlite or postgresql)",
    )
    database_pool_size: int = Field(default=20, description="Database connection pool size")
    database_echo: bool = Field(default=False, description="Echo SQL queries")

    # PostgreSQL-specific settings (used when database_type is postgresql)
    database_host: str = Field(default="localhost", description="PostgreSQL host")
    database_port: int = Field(default=5432, description="PostgreSQL port")
    database_name: str = Field(default="agentspy", description="PostgreSQL database name")
    database_user: str = Field(default="agentspy_user", description="PostgreSQL username")
    database_password: str = Field(default="", description="PostgreSQL password")
    database_ssl_mode: str = Field(default="prefer", description="PostgreSQL SSL mode")
    database_max_connections: int = Field(default=20, description="PostgreSQL max connections")

    # API Settings
    api_prefix: str = Field(default="/api/v1", description="API route prefix")
    api_title: str = Field(default="Agent Spy API", description="API documentation title")
    api_description: str = Field(
        default=("LangSmith-compatible observability layer for AI agents and LangChain applications"),
        description="API documentation description",
    )

    # Authentication Settings
    api_keys: list[str] | None = Field(default=None, description="Comma-separated list of valid API keys")
    require_auth: bool = Field(default=False, description="Require authentication for all endpoints")

    # CORS Settings
    cors_origins: list[str] | str = Field(default=["*"], description="Allowed CORS origins")
    cors_credentials: bool = Field(default=True, description="Allow credentials in CORS requests")
    cors_methods: list[str] | str = Field(default=["*"], description="Allowed CORS methods")
    cors_headers: list[str] | str = Field(default=["*"], description="Allowed CORS headers")

    # LangSmith Compatibility Settings
    langsmith_endpoint_base: str = Field(default="/api/v1", description="Base path for LangSmith-compatible endpoints")
    support_legacy_endpoints: bool = Field(default=True, description="Support legacy LangChain endpoint formats")

    # Performance Settings
    max_trace_size_mb: int = Field(default=10, description="Maximum trace size in MB")
    request_timeout: int = Field(default=30, description="Request timeout in seconds")

    # WebSocket Settings
    websocket_enabled: bool = Field(default=True, description="Enable WebSocket support")
    websocket_max_connections: int = Field(default=100, description="Maximum WebSocket connections")
    websocket_heartbeat_interval: int = Field(default=30, description="WebSocket heartbeat interval in seconds")

    # OpenTelemetry Settings
    otlp_grpc_enabled: bool = Field(default=True, description="Enable OTLP gRPC receiver")
    otlp_grpc_host: str = Field(default="0.0.0.0", description="OTLP gRPC server host")  # nosec B104
    otlp_grpc_port: int = Field(default=4317, description="OTLP gRPC server port")
    otlp_http_enabled: bool = Field(default=True, description="Enable OTLP HTTP receiver")
    otlp_http_path: str = Field(default="/v1/traces", description="OTLP HTTP endpoint path")

    # OTLP Forwarder Settings
    otlp_forwarder_enabled: bool = Field(default=False, description="Enable OTLP forwarder")
    otlp_forwarder_endpoint: str = Field(default="", description="OTLP forwarder endpoint URL")
    otlp_forwarder_protocol: str = Field(default="grpc", description="OTLP forwarder protocol (http or grpc)")
    otlp_forwarder_service_name: str = Field(default="agent-spy-forwarder", description="Service name for forwarded traces")
    otlp_forwarder_timeout: int = Field(default=30, description="OTLP forwarder timeout in seconds")
    otlp_forwarder_retry_count: int = Field(default=3, description="OTLP forwarder retry count")
    otlp_forwarder_headers: dict[str, str] | None = Field(default=None, description="OTLP forwarder headers")

    # Logging Settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")
    log_file: str | None = Field(default=None, description="Log file path")

    @field_validator("api_keys", mode="before")
    @classmethod
    def parse_api_keys(cls, v: str | None) -> list[str] | None:
        """Parse comma-separated API keys from environment variable."""
        if isinstance(v, str) and v:
            return [key.strip() for key in v.split(",") if key.strip()]
        return v if isinstance(v, list) else None

    @field_validator("cors_origins", "cors_methods", "cors_headers", mode="before")
    @classmethod
    def parse_cors_list(cls, v: str | list[str]) -> list[str]:
        """Parse CORS settings from environment variable."""
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            # Handle comma-separated values
            return [item.strip() for item in v.split(",") if item.strip()]
        # v is already a list[str] at this point
        return v

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = ["development", "staging", "production", "test"]
        if v.lower() not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v.lower()

    @field_validator("database_type")
    @classmethod
    def validate_database_type(cls, v: str) -> str:
        """Validate database type value."""
        allowed = ["sqlite", "postgresql"]
        if v.lower() not in allowed:
            raise ValueError(f"Database type must be one of {allowed}")
        return v.lower()

    @field_validator("database_ssl_mode")
    @classmethod
    def validate_ssl_mode(cls, v: str) -> str:
        """Validate PostgreSQL SSL mode."""
        allowed = ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]
        if v.lower() not in allowed:
            raise ValueError(f"SSL mode must be one of {allowed}")
        return v.lower()

    @field_validator("otlp_forwarder_protocol")
    @classmethod
    def validate_otlp_protocol(cls, v: str) -> str:
        """Validate OTLP protocol value."""
        allowed = ["http", "grpc"]
        if v.lower() not in allowed:
            raise ValueError(f"OTLP protocol must be one of {allowed}")
        return v.lower()

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"

    @property
    def is_test(self) -> bool:
        """Check if running in test mode."""
        return self.environment == "test"

    # New naming convention properties for backward compatibility
    @property
    def backend_host(self) -> str:
        """Get backend host (alias for host)."""
        return self.host

    @property
    def backend_port(self) -> int:
        """Get backend port (alias for port)."""
        return self.port

    @property
    def db_host(self) -> str:
        """Get database host (alias for database_host)."""
        return self.database_host

    @property
    def db_port(self) -> int:
        """Get database port (alias for database_port)."""
        return self.database_port

    @property
    def db_name(self) -> str:
        """Get database name (alias for database_name)."""
        return self.database_name

    @property
    def db_user(self) -> str:
        """Get database user (alias for database_user)."""
        return self.database_user

    @property
    def db_password(self) -> str:
        """Get database password (alias for database_password)."""
        return self.database_password

    @property
    def backend_otlp_grpc_host(self) -> str:
        """Get OTLP gRPC host (alias for otlp_grpc_host)."""
        return self.otlp_grpc_host

    @property
    def backend_otlp_grpc_port(self) -> int:
        """Get OTLP gRPC port (alias for otlp_grpc_port)."""
        return self.otlp_grpc_port

    def get_database_url(self) -> str:
        """Get the database URL, constructing it from components if needed."""
        # If a direct URL is provided, use it
        if self.database_url and not self.database_url.startswith("sqlite+aiosqlite:///./agentspy.db"):
            return self.database_url

        # Construct URL based on database type
        if self.database_type == "postgresql":
            # Build PostgreSQL URL from components
            password_part = f":{self.database_password}" if self.database_password else ""
            return f"postgresql+asyncpg://{self.database_user}{password_part}@{self.database_host}:{self.database_port}/{self.database_name}"
        else:
            # Default SQLite URL
            return self.database_url

    @classmethod
    def load_env_file_priority(cls) -> dict[str, str]:
        """Load environment variables with environment variables taking priority over .env file."""
        env_vars = {}

        # First, load from .env file as defaults
        env_file = Path(".env")
        if env_file.exists():
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key] = value

        # Then, override with environment variables (environment variables take priority)
        for key, value in os.environ.items():
            env_vars[key] = value

        # Handle new naming convention by mapping to old field names
        # This allows both old and new environment variable names to work
        env_mapping = {
            "BACKEND_HOST": "HOST",
            "BACKEND_PORT": "PORT",
            "DB_HOST": "DATABASE_HOST",
            "DB_PORT": "DATABASE_PORT",
            "DB_NAME": "DATABASE_NAME",
            "DB_USER": "DATABASE_USER",
            "DB_PASSWORD": "DATABASE_PASSWORD",
            "BACKEND_OTLP_GRPC_HOST": "OTLP_GRPC_HOST",
            "BACKEND_OTLP_GRPC_PORT": "OTLP_GRPC_PORT",
        }

        # Apply mapping for new environment variables
        # New naming convention takes priority over old naming convention
        for new_key, old_key in env_mapping.items():
            if new_key in env_vars:
                env_vars[old_key] = env_vars[new_key]

        return env_vars


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    # Check if we're in a test environment
    if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TESTING"):
        # In test environment, prioritize environment variables over .env file
        return Settings(_env_file=None)

    # Use custom environment loading to prioritize .env file
    env_vars = Settings.load_env_file_priority()

    # Temporarily set environment variables with .env file priority
    original_env = dict(os.environ)
    try:
        # Clear existing environment variables that are in .env file
        for key in env_vars:
            if key in os.environ:
                del os.environ[key]

        # Set environment variables with .env file values first
        for key, value in env_vars.items():
            os.environ[key] = value

        # Create settings instance
        return Settings()
    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)
