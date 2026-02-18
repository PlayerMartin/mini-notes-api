from pydantic import BaseModel, Field


class WebhookNote(BaseModel):
    source: str = Field(min_length=1)
    message: str = Field(min_length=1)
    tags: list[str] = []
