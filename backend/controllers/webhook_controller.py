import os
from typing import Annotated

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends, Header
from starlette import status
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from config.di import get_note_repo, get_webhook_repo
from models.notes import CreateNote, Note
from models.webhooks import WebhookNote
from repositories.note_repository import NoteRepository
from repositories.webhook_repository import WebhookRepository

router = APIRouter(prefix="/webhooks")


@router.post("/note", status_code=HTTP_201_CREATED)
async def create_note(
    note: WebhookNote,
    x_webhook_token: Annotated[str | None, Header()] = None,
    note_repo: NoteRepository = Depends(get_note_repo),
    webhook_repo: WebhookRepository = Depends(get_webhook_repo),
) -> Note:
    if x_webhook_token != os.getenv("WEBHOOK_TOKEN"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid X-Webhook-Token header",
        )

    tags = note.tags
    tags.append(f"source:{note.source}")
    new_note = await note_repo.create(
        CreateNote(title=note.message[:40], content=note.message, tags=tags)
    )

    webhook_repo.log(note)
    return new_note


@router.get("/log", status_code=HTTP_200_OK)
async def get_logs(
    webhook_repo: WebhookRepository = Depends(get_webhook_repo),
) -> list[dict]:
    return await webhook_repo.get_all()
