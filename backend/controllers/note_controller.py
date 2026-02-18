from typing import Annotated

from cachetools import TTLCache
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.params import Query
from starlette import status

from config.di import get_note_repo
from models.notes import CreateNote, Note, UpdateNote
from repositories.note_repository import NoteRepository

router = APIRouter(prefix="/notes")

_create_cache: TTLCache = TTLCache(maxsize=1000, ttl=86400)
_update_cache: TTLCache = TTLCache(maxsize=1000, ttl=86400)


@router.get("")
async def get_notes(
    q: str | None = None,
    tag: str | None = None,
    limit: Annotated[int, Query(le=5, ge=0)] = 0,
    offset: Annotated[int, Query(ge=0)] = 0,
    note_repo: NoteRepository = Depends(get_note_repo),
) -> list[Note]:
    return await note_repo.get_all(q, tag, limit, offset)


@router.get("/{id}")
async def get_note(id: int, note_repo: NoteRepository = Depends(get_note_repo)) -> Note:
    note = await note_repo.get(id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )
    return note


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_note(
    note: CreateNote,
    note_repo: NoteRepository = Depends(get_note_repo),
    idempotency_key: Annotated[str | None, Header()] = None,
) -> Note:
    if idempotency_key in _create_cache:
        return _create_cache[idempotency_key]

    res = await note_repo.create(note)
    _create_cache[idempotency_key] = res
    return res


@router.post("/{id}", status_code=status.HTTP_200_OK)
async def update_note(
    id: int,
    note: UpdateNote,
    note_repo: NoteRepository = Depends(get_note_repo),
    idempotency_key: Annotated[str | None, Header()] = None,
) -> Note:
    if idempotency_key in _update_cache:
        return _update_cache[idempotency_key]

    res = await note_repo.update(id, note)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )
    _update_cache[idempotency_key] = res
    return res


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(id: int, note_repo: NoteRepository = Depends(get_note_repo)):
    note = await note_repo.delete(id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )
