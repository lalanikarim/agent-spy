"""Configuration management for Agent Spy."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
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
    database_pool_size: int = Field(default=20, description="Database connection pool size")
    database_echo: bool = Field(default=False, description="Echo SQL queries")

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


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
