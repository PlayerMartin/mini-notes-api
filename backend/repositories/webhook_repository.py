from collections import deque

from config.now import now
from models.webhooks import WebhookNote


class WebhookRepository:
    def __init__(self):
        self.logs: deque = deque(maxlen=20)

    def log(self, note: WebhookNote) -> None:
        self.logs.append({**note.model_dump(), "datetime": now()})

    async def get_all(self) -> list[dict]:
        return list(self.logs)
