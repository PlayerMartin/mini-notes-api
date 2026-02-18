from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from config.di import get_note_repo
from models.notes import CreateNote, Note
from repositories.note_repository import NoteRepository

router = APIRouter(prefix="/notes")


@router.get("")
async def get_notes(
    q: str | None = None,
    tag: str | None = None,
    note_repo: NoteRepository = Depends(get_note_repo),
) -> list[Note]:
    return await note_repo.get_all(q, tag)


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
    note: CreateNote, note_repo: NoteRepository = Depends(get_note_repo)
) -> Note:
    return await note_repo.create(note)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(id: int, note_repo: NoteRepository = Depends(get_note_repo)):
    note = await note_repo.delete(id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )
