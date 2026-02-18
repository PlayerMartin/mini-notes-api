import os

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        db_url = os.getenv("DB_URL")
        if not db_url:
            raise RuntimeError("DB_URL environment variable is not set")
        _engine = create_async_engine(db_url, echo=True)
    return _engine


async def create_db():
    engine = get_engine()
    async with engine.connect() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.commit()
