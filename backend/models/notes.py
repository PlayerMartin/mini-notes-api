from datetime import datetime

from pydantic import BaseModel, Field


class CreateNote(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = ""
    tags: list[str] = []


class Note(CreateNote):
    id: int
    created_at: datetime
