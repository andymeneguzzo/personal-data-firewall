"""
Database configuration and session management.

This module handles SQLAlchemy database setup, session creation,
and provides utilities for database operations.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from app.core.config import settings

# Create async engine for SQLite
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Enable SQL logging for development
    poolclass=StaticPool,  # Use static pool for SQLite
    connect_args={"check_same_thread": False}
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for all models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency function to get database session.
    
    Yields:
        AsyncSession: Database session for dependency injection
        
    Example:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            # Use db session here
            pass
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database with tables and seed data.
    Called during application startup.
    """
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database initialized successfully")


async def close_db():
    """
    Close database connections.
    Called during application shutdown.
    """
    await engine.dispose()
    print("🛑 Database connections closed")