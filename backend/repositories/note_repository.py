from datetime import datetime

from models.notes import CreateNote, Note

DB = {}
ID_gen: int = 0


def get_all(q: str | None = None, tag: str | None = None) -> list[Note]:
    notes = list(DB.values())
    if tag:
        notes = [n for n in notes if tag in n.tags]
    if q:
        q = q.lower()
        notes = [n for n in notes if q in n.title.lower() or q in n.content.lower()]
    return notes


def get_by_id(id: int) -> Note | None:
    return DB.get(id, None)


def create(note: CreateNote) -> Note:
    global ID_gen
    new_note = Note(**note.model_dump(), id=ID_gen, created_at=now())
    ID_gen += 1
    DB[new_note.id] = new_note
    return new_note


def delete(id: int) -> Note | None:
    return DB.pop(id, None)


def now() -> datetime:
    return datetime.now()
