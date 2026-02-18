from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from config.db_config import get_engine
from repositories.note_repository import NoteRepository


async def get_session():
    async with AsyncSession(get_engine()) as session:
        yield session


def get_note_repo(session: AsyncSession = Depends(get_session)) -> NoteRepository:
    return NoteRepository(session)
