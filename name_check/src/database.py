"""
Database configuration and utility functions module.

This module provides functionality to configure the database, manage sessions,
and interact with the database asynchronously.
"""

import os
from typing import AsyncGenerator
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy import select
from models import ServiceType
from base import Base

# Load environment variables
load_dotenv()

DATABASE_URL = (
    f"postgresql+asyncpg://{os.getenv('DEV_POSTGRES_USER')}:{os.getenv('DEV_POSTGRES_PASSWORD')}"
    f"@{os.getenv('DEV_POSTGRES_HOST')}/{os.getenv('DEV_POSTGRES_DB')}"
)

# Create an async engine
engine: Engine = create_async_engine(DATABASE_URL, echo=False)

# Session factory for async sessions
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

async def initialize_db():
    """
    Initialize the database and create tables asynchronously.

    This function uses the SQLAlchemy engine to create all tables defined in
    the metadata.

    Returns:
        None
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get the database session asynchronously.

    This function provides an async session generator that yields a new session
    for database operations and ensures it is properly closed after use.

    Yields:
        AsyncSession: An async database session instance.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_service_types(session: AsyncSession):
    """
    Fetch service types from the database asynchronously.

    This function retrieves all service types from the database using the given
    async session and returns a list of ServiceType instances.

    Args:
        session (AsyncSession): Async database session.

    Returns:
        List[ServiceType]: List of service type instances.
    """
    stmt = select(ServiceType)
    result = await session.execute(stmt)
    return result.scalars().all()
