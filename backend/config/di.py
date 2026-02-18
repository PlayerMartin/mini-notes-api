from fastapi import Depends, FastAPI
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.requests import Request

from config.db_config import get_engine
from repositories.note_repository import NoteRepository
from repositories.webhook_repository import WebhookRepository


def register_singletons(app: FastAPI):
    app.state.webhook_repo = WebhookRepository()


async def get_session():
    async with AsyncSession(get_engine()) as session:
        yield session


def get_note_repo(session: AsyncSession = Depends(get_session)) -> NoteRepository:
    return NoteRepository(session)


def get_webhook_repo(request: Request) -> WebhookRepository:
    return request.app.state.webhook_repo
