from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from config.di import get_note_repo, get_webhook_repo
from main import app
from models.notes import CreateNote, Note
from repositories.webhook_repository import WebhookRepository

WEBHOOK_TOKEN = "test-secret-token"


@pytest.fixture()
def webhook_repo():
    """A real WebhookRepository (in-memory deque, no DB needed)."""
    return WebhookRepository()


@pytest.fixture()
def mock_note_repo():
    """
    A mock NoteRepository that simulates create + get_all behaviour.

    * `create` stores notes in an internal list and returns them with an id.
    * `get_all` returns everything that was stored.
    """
    repo = AsyncMock()
    stored_notes: list[Note] = []

    async def fake_create(note: CreateNote) -> Note:
        db_note = Note(
            id=len(stored_notes) + 1,
            title=note.title,
            content=note.content,
            tags=note.tags,
            created_at=datetime(2026, 1, 1, 12, 0, 0),
        )
        stored_notes.append(db_note)
        return db_note

    async def fake_get_all(q=None, tag=None, limit=3, offset=0):
        return stored_notes

    repo.create.side_effect = fake_create
    repo.get_all.side_effect = fake_get_all
    return repo


@pytest.fixture()
def client(mock_note_repo, webhook_repo):
    """
    TestClient with both NoteRepository and WebhookRepository overridden
    and the WEBHOOK_TOKEN env var set.
    """
    app.dependency_overrides[get_note_repo] = lambda: mock_note_repo
    app.dependency_overrides[get_webhook_repo] = lambda: webhook_repo
    with patch.dict("os.environ", {"WEBHOOK_TOKEN": WEBHOOK_TOKEN}):
        yield TestClient(app)
    app.dependency_overrides.clear()


class TestWebhookCreatesAndRetrievesNote:

    def test_webhook_creates_note_and_get_notes_returns_it(
        self,
        client: TestClient,
        mock_note_repo,
    ):
        """
        1. Call POST /webhooks/note with a valid payload + token.
        2. Verify 201 and the returned note.
        3. Call GET /notes and confirm the note appears in the list.
        """
        # --- Step 1: Create via webhook ---
        webhook_payload = {
            "source": "monitoring",
            "message": "Server CPU at 95% — investigate immediately",
            "tags": ["alert", "infra"],
        }

        create_resp = client.post(
            "/webhooks/note",
            json=webhook_payload,
            headers={"X-Webhook-Token": WEBHOOK_TOKEN},
        )

        assert create_resp.status_code == 201
        created = create_resp.json()
        assert created["id"] == 1
        # title is truncated to first 40 chars of message
        assert created["title"] == webhook_payload["message"][:40]
        assert created["content"] == webhook_payload["message"]
        # tags should include the originals + source:monitoring
        assert "alert" in created["tags"]
        assert "infra" in created["tags"]
        assert "source:monitoring" in created["tags"]

        # --- Step 2: Retrieve via GET /notes ---
        get_resp = client.get("/notes")

        assert get_resp.status_code == 200
        notes = get_resp.json()
        assert len(notes) == 1
        assert notes[0]["id"] == created["id"]
        assert notes[0]["title"] == created["title"]
        assert notes[0]["content"] == created["content"]

    def test_webhook_without_token_returns_401(self, client: TestClient):
        """Missing or wrong token must result in 401."""
        response = client.post(
            "/webhooks/note",
            json={
                "source": "ci",
                "message": "Build failed",
            },
        )

        assert response.status_code == 401

    def test_webhook_with_wrong_token_returns_401(self, client: TestClient):
        """An incorrect token must also result in 401."""
        response = client.post(
            "/webhooks/note",
            json={"source": "ci", "message": "Build failed"},
            headers={"X-Webhook-Token": "wrong-token"},
        )

        assert response.status_code == 401

    def test_webhook_invalid_payload_returns_422(self, client: TestClient):
        """Missing required fields must return 422."""
        response = client.post(
            "/webhooks/note",
            json={},
            headers={"X-Webhook-Token": WEBHOOK_TOKEN},
        )

        assert response.status_code == 422

    def test_webhook_logs_entry(
        self,
        client: TestClient,
        webhook_repo: WebhookRepository,
    ):
        """After a successful webhook call the entry must appear in the log."""
        client.post(
            "/webhooks/note",
            json={"source": "ci", "message": "Deployment succeeded", "tags": []},
            headers={"X-Webhook-Token": WEBHOOK_TOKEN},
        )

        assert len(webhook_repo.logs) == 1
        assert webhook_repo.logs[0]["source"] == "ci"

    def test_multiple_webhooks_all_retrievable(
        self,
        client: TestClient,
        mock_note_repo,
    ):
        """Creating several notes via webhook — all should appear in GET /notes."""
        for i in range(3):
            client.post(
                "/webhooks/note",
                json={
                    "source": f"svc-{i}",
                    "message": f"Event number {i}",
                    "tags": [],
                },
                headers={"X-Webhook-Token": WEBHOOK_TOKEN},
            )

        notes = client.get("/notes").json()
        assert len(notes) == 3
        # Verify IDs are sequential
        assert [n["id"] for n in notes] == [1, 2, 3]


class TestWebhookValidationMissingFields:
    """Test webhook validation for missing/empty required fields."""

    def test_webhook_missing_content_returns_422(self, client: TestClient):
        """Missing message (content) must return 422."""
        response = client.post(
            "/webhooks/note",
            json={
                "source": "monitoring",
                "tags": ["alert"],
            },
            headers={"X-Webhook-Token": WEBHOOK_TOKEN},
        )

        assert response.status_code == 422

    def test_webhook_empty_content_returns_422(self, client: TestClient):
        """Empty message (content) must return 422."""
        response = client.post(
            "/webhooks/note",
            json={
                "source": "monitoring",
                "message": "",
                "tags": ["alert"],
            },
            headers={"X-Webhook-Token": WEBHOOK_TOKEN},
        )

        assert response.status_code == 422

    def test_webhook_missing_source_returns_422(self, client: TestClient):
        """Missing source must return 422."""
        response = client.post(
            "/webhooks/note",
            json={
                "message": "Something happened",
                "tags": ["event"],
            },
            headers={"X-Webhook-Token": WEBHOOK_TOKEN},
        )

        assert response.status_code == 422

    def test_webhook_empty_source_returns_422(self, client: TestClient):
        """Empty source must return 422."""
        response = client.post(
            "/webhooks/note",
            json={
                "source": "",
                "message": "Something happened",
                "tags": ["event"],
            },
            headers={"X-Webhook-Token": WEBHOOK_TOKEN},
        )

        assert response.status_code == 422

    def test_webhook_missing_tags_defaults_to_empty(self, client: TestClient):
        """Missing tags should default to empty list and succeed."""
        response = client.post(
            "/webhooks/note",
            json={
                "source": "monitoring",
                "message": "Alert triggered",
            },
            headers={"X-Webhook-Token": WEBHOOK_TOKEN},
        )

        assert response.status_code == 201
        created = response.json()
        # Should still have source:monitoring tag added
        assert "source:monitoring" in created["tags"]

    def test_webhook_empty_tags_is_valid(self, client: TestClient):
        """Empty tags list should be valid."""
        response = client.post(
            "/webhooks/note",
            json={
                "source": "ci",
                "message": "Build completed",
                "tags": [],
            },
            headers={"X-Webhook-Token": WEBHOOK_TOKEN},
        )

        assert response.status_code == 201
        created = response.json()
        assert "source:ci" in created["tags"]

    def test_webhook_with_all_fields_succeeds(self, client: TestClient):
        """Complete payload with all fields should succeed."""
        response = client.post(
            "/webhooks/note",
            json={
                "source": "api",
                "message": "Complete webhook payload",
                "tags": ["automated", "test"],
            },
            headers={"X-Webhook-Token": WEBHOOK_TOKEN},
        )

        assert response.status_code == 201
        created = response.json()
        assert created["content"] == "Complete webhook payload"
        assert "automated" in created["tags"]
        assert "test" in created["tags"]
        assert "source:api" in created["tags"]
