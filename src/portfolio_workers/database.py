from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncIterator, Annotated
from fastapi import Depends

from portfolio_workers.config import get_settings

settings = get_settings()

URL_DATABASE = f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}@{settings.db_link}/{settings.db_name}"

engine = create_async_engine(URL_DATABASE, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session

DbSession = Annotated[AsyncSession, Depends(get_db)]