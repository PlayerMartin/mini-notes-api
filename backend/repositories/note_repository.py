from datetime import datetime
from typing import Optional

from sqlmodel import col, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from models.notes import CreateNote, Note


class NoteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, note_id: int) -> Optional[Note]:
        return await self.session.get(Note, note_id)

    async def get_all(self, q: str | None = None, tag: str | None = None) -> list[Note]:
        statement = select(Note)

        if tag:
            statement = statement.where(col(Note.tags).contains([tag]))

        if q:
            statement = statement.where(
                or_(col(Note.title).ilike(f"%{q}%"), col(Note.content).ilike(f"%{q}%"))
            )

        notes = await self.session.exec(statement)
        return list(notes.all())

    async def create(self, note: CreateNote) -> Note:
        db_note = Note(**note.model_dump(), created_at=now())
        self.session.add(db_note)
        await self.session.commit()
        await self.session.refresh(db_note)
        return db_note

    # def update(self, hero_id: int, data: HeroUpdate) -> Optional[Hero]:
    #     hero = self.get(hero_id)
    #     if not hero:
    #         return None
    #     hero.sqlmodel_update(data.model_dump(exclude_unset=True))
    #     self.session.add(hero)
    #     self.session.commit()
    #     self.session.refresh(hero)
    #     return hero

    async def delete(self, note_id: int) -> bool:
        note = await self.get(note_id)
        if not note:
            return False
        await self.session.delete(note)
        await self.session.commit()
        return True


def now() -> datetime:
    return datetime.now()
