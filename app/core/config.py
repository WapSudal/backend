"""Application configuration using Pydantic Settings V2.

Manages all environment variables with type validation and fail-fast strategy.
"""

from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.
    
    Attributes:
        ENVIRONMENT: Current environment (development, staging, production)
        DEBUG: Enable debug mode
        DATABASE_URL: PostgreSQL connection string
        
        # Database connection pool settings (auto-configured based on environment)
        DB_POOL_SIZE: Base connection pool size
        DB_MAX_OVERFLOW: Maximum overflow connections
        DB_POOL_TIMEOUT: Connection acquisition timeout (seconds)
        DB_POOL_RECYCLE: Connection recycle time (seconds)
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    # Application settings
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    
    # Database settings
    DATABASE_URL: PostgresDsn
    
    # Connection pool settings (optional overrides)
    DB_POOL_SIZE: int | None = None
    DB_MAX_OVERFLOW: int | None = None
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800  # 30 minutes
    
    @computed_field
    @property
    def pool_size(self) -> int:
        """Get connection pool size based on environment."""
        if self.DB_POOL_SIZE is not None:
            return self.DB_POOL_SIZE
        # Auto-configure based on environment
        return {
            "development": 5,
            "staging": 10,
            "production": 20,
        }.get(self.ENVIRONMENT, 5)
    
    @computed_field
    @property
    def max_overflow(self) -> int:
        """Get max overflow connections based on environment."""
        if self.DB_MAX_OVERFLOW is not None:
            return self.DB_MAX_OVERFLOW
        # Auto-configure based on environment
        return {
            "development": 5,
            "staging": 10,
            "production": 10,
        }.get(self.ENVIRONMENT, 5)
    
    @computed_field
    @property
    def database_url_async(self) -> str:
        """Get async database URL with psycopg driver."""
        url = str(self.DATABASE_URL)
        # Ensure we're using the async-compatible psycopg dialect
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg://", 1)
        return url
    
    @computed_field
    @property
    def database_url_sync(self) -> str:
        """Get sync database URL for Alembic migrations."""
        url = str(self.DATABASE_URL)
        # Use standard postgresql:// for sync operations
        if url.startswith("postgresql+psycopg://"):
            return url.replace("postgresql+psycopg://", "postgresql://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.
    
    Using lru_cache ensures settings are loaded only once.
    """
    return Settings()


# Global settings instance
settings = get_settings()
