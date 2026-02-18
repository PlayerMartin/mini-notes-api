import os
from typing import Annotated

from fastapi import APIRouter, HTTPException
from fastapi.params import Header
from starlette import status
from starlette.status import HTTP_201_CREATED

from models.notes import CreateNote, Note
from models.webhooks import WebhookNote
from repositories import note_repository

router = APIRouter(prefix="/webhooks")


@router.post("/note", status_code=HTTP_201_CREATED)
def create_note(
    note: WebhookNote, x_webhook_token: Annotated[str | None, Header()] = None
) -> Note:
    if x_webhook_token != os.getenv("WEBHOOK_TOKEN"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid X-Webhook-Token header",
        )

    tags = note.tags
    tags.append(f"source:{note.source}")
    new_note = CreateNote(title=note.message[:40], content=note.message, tags=tags)
    return note_repository.create(new_note)
