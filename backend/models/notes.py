from datetime import datetime
from typing import Optional

from sqlalchemy import Column, VARCHAR
from sqlalchemy.dialects.postgresql import ARRAY
from sqlmodel import Field, SQLModel


class NoteBase(SQLModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = ""
    tags: list[str] = Field(default=[], sa_column=Column(ARRAY(VARCHAR)))


class UpdateNote(NoteBase):
    pass


class CreateNote(NoteBase):
    pass


class Note(NoteBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime
