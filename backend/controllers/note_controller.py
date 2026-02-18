from fastapi import APIRouter, HTTPException
from starlette import status

from models.notes import Note, CreateNote
import repositories.note_repository as note_repository

router = APIRouter(prefix="/notes")


@router.get("")
async def get_notes(q: str | None = None, tag: str | None = None) -> list[Note]:
    return note_repository.get_all(q, tag)


@router.get("/{id}")
async def get_note(id: int) -> Note:
    note = note_repository.get_by_id(id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )
    return note


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_note(note: CreateNote) -> Note:
    return note_repository.create(note)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(id: int):
    note = note_repository.delete(id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )
