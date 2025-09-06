"""Simplified configuration management for Agent Spy."""

import os
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
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
    host: str = Field(default="127.0.0.1", description="Server host")
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
    database_ssl_mode: str = Field(default="prefer", description="PostgreSQL SSL mode")
    database_max_connections: int = Field(default=20, description="PostgreSQL max connections")

    # PostgreSQL-specific settings
    database_host: str = Field(default="localhost", description="PostgreSQL host")
    database_port: int = Field(default=5432, description="PostgreSQL port")
    database_name: str = Field(default="agentspy", description="PostgreSQL database name")
    database_user: str = Field(default="agentspy_user", description="PostgreSQL username")
    database_password: str = Field(default="", description="PostgreSQL password")

    # API Settings
    api_title: str = Field(default="Agent Spy API", description="API documentation title")
    api_description: str = Field(
        default=("LangSmith-compatible observability layer for AI agents and LangChain applications"),
        description="API documentation description",
    )

    # CORS Settings
    cors_origins: list[str] | str = Field(default=["*"], description="Allowed CORS origins")
    cors_credentials: bool = Field(default=True, description="Allow credentials in CORS requests")
    cors_methods: list[str] | str = Field(default=["*"], description="Allowed CORS methods")
    cors_headers: list[str] | str = Field(default=["*"], description="Allowed CORS headers")

    # LangSmith Compatibility Settings
    langsmith_endpoint_base: str = Field(default="/api/v1", description="Base path for LangSmith-compatible endpoints")

    # WebSocket Settings
    websocket_enabled: bool = Field(default=True, description="Enable WebSocket support")

    # OpenTelemetry Settings
    otlp_grpc_enabled: bool = Field(default=True, description="Enable OTLP gRPC receiver")
    otlp_grpc_host: str = Field(default="127.0.0.1", description="OTLP gRPC server host")
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
    # New forwarder tunables (env-backed)
    otlp_forwarder_insecure: bool = Field(default=True, description="Use insecure (non-TLS) exporter when true")
    forwarder_debounce_seconds: float = Field(default=5.0, description="Debounce window for grouped forwarding")
    forward_run_timeout_seconds: float = Field(default=30.0, description="Per-run forwarding timeout in seconds")
    forwarder_max_synthetic_spans: int = Field(default=10, description="Max synthetic step spans to emit")
    forwarder_attr_max_str: int = Field(default=500, description="Max length for string attributes")
    forwarder_attr_max_kv_str: int = Field(default=200, description="Max length for key-value attribute values")
    forwarder_attr_max_list_items: int = Field(default=5, description="Max number of list items to include as attributes")

    # Logging Settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")
    log_file: str | None = Field(default=None, description="Log file path")

    # OTLP gRPC server tunables
    otlp_grpc_max_workers: int = Field(default=10, description="gRPC server worker threads")
    otlp_grpc_max_msg_mb: int = Field(default=50, description="Max gRPC message size in MB")
    otlp_grpc_stop_grace_seconds: int = Field(default=5, description="gRPC server stop grace period seconds")

    # DB init retry/backoff
    db_init_max_retries: int = Field(default=3, description="DB init max retries")
    db_init_initial_delay_seconds: int = Field(default=2, description="DB init initial backoff seconds")

    # Stale run cleanup default
    stale_run_timeout_minutes_default: int = Field(default=30, description="Default timeout to mark running traces failed")

    @field_validator("cors_origins", "cors_methods", "cors_headers", mode="before")
    @classmethod
    def parse_cors_list(cls, v: str | list[str]) -> list[str]:
        """Parse CORS settings from environment variable."""
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [item.strip() for item in v.split(",") if item.strip()]
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

    def get_database_url(self) -> str:
        """Get the database URL, constructing it from components if needed."""
        # If a direct URL is provided and it's not the default SQLite URL, use it
        if self.database_url and not self.database_url.startswith("sqlite+aiosqlite:///./agentspy.db"):
            return self.database_url

        # Construct URL based on database type
        if self.database_type == "postgresql":
            # Build PostgreSQL URL from components
            password_part = (
                f":{self.database_password}" if hasattr(self, "database_password") and self.database_password else ""
            )
            return f"postgresql+asyncpg://{self.database_user}{password_part}@{self.database_host}:{self.database_port}/{self.database_name}"
        else:
            # Default SQLite URL
            return self.database_url


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    # Check if we're in a test environment
    if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TESTING"):
        return Settings(_env_file=None)

    # Use standard Pydantic settings loading
    return Settings()
