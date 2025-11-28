"""Database connection and session management.

Provides async database engine and session factory using SQLAlchemy 2.0
with psycopg (v3) driver for optimal async performance.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.core.config import settings


def create_engine() -> AsyncEngine:
    """Create async database engine with environment-specific pool settings.
    
    Returns:
        AsyncEngine: Configured SQLAlchemy async engine
    """
    # Use NullPool for testing or when pool is not needed
    if settings.ENVIRONMENT == "development" and settings.DEBUG:
        return create_async_engine(
            settings.database_url_async,
            echo=True,  # SQL logging in debug mode
            poolclass=NullPool,
        )
    
    return create_async_engine(
        settings.database_url_async,
        echo=settings.DEBUG,
        future=True,
        pool_size=settings.pool_size,
        max_overflow=settings.max_overflow,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,  # Verify connection is alive before use
    )


# Global engine instance
engine = create_engine()

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,  # Required for async - prevents lazy loading issues
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection function for database sessions.
    
    Provides a database session that automatically handles
    commit/rollback and cleanup.
    
    Yields:
        AsyncSession: Database session for the request
        
    Example:
        ```python
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
        ```
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
