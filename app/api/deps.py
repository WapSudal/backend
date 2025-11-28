"""FastAPI dependency injection functions.

Provides reusable dependencies for database sessions, authentication,
and other cross-cutting concerns.
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection function for database sessions.
    
    Provides a database session that automatically handles
    commit/rollback and cleanup.
    
    Yields:
        AsyncSession: Database session for the request
        
    Example:
        ```python
        from src.api.deps import DbSession
        
        @app.get("/items")
        async def get_items(db: DbSession):
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


# Type alias for cleaner dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]
