from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from config.di import get_note_repo
from controllers.note_controller import _create_cache
from main import app
from models.notes import Note


@pytest.fixture(autouse=True)
def clear_idempotency_cache():
    """Clean idempotency cache before and after every test."""
    _create_cache.clear()
    yield
    _create_cache.clear()


@pytest.fixture()
def mock_repo():
    """Mock NoteRepository with a default create return value."""
    repo = AsyncMock()
    repo.create.return_value = Note(
        id=1,
        title="Test Note",
        content="Some content",
        tags=["tag1"],
        created_at=datetime(2026, 1, 1, 12, 0, 0),
    )
    return repo


@pytest.fixture()
def client(mock_repo):
    """TestClient with the NoteRepository dependency overridden."""
    app.dependency_overrides[get_note_repo] = lambda: mock_repo
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestCreateNoteSuccess:

    # valid note → 201
    def test_create_note_returns_201(self, client: TestClient):
        response = client.post(
            "/notes",
            json={
                "title": "Test Note",
                "content": "Some content",
                "tags": ["tag1"],
            },
        )

        assert response.status_code == 201

    # response body contains all expected fields
    def test_create_note_returns_note_body(self, client: TestClient):
        response = client.post(
            "/notes",
            json={
                "title": "Test Note",
                "content": "Some content",
                "tags": ["tag1"],
            },
        )

        data = response.json()
        assert data["id"] == 1
        assert data["title"] == "Test Note"
        assert data["content"] == "Some content"
        assert data["tags"] == ["tag1"]
        assert "created_at" in data

    # repo.create is called exactly once
    def test_create_note_calls_repo(self, client: TestClient, mock_repo):
        client.post(
            "/notes",
            json={
                "title": "Test Note",
                "content": "Some content",
                "tags": ["tag1"],
            },
        )

        mock_repo.create.assert_awaited_once()

    # content defaults to "" when omitted
    def test_create_note_with_empty_content(self, client: TestClient, mock_repo):
        mock_repo.create.return_value = Note(
            id=2,
            title="Only Title",
            content="",
            tags=[],
            created_at=datetime(2026, 1, 1, 12, 0, 0),
        )

        response = client.post("/notes", json={"title": "Only Title"})

        assert response.status_code == 201
        assert response.json()["content"] == ""

    # tags default to [] when omitted
    def test_create_note_with_empty_tags(self, client: TestClient, mock_repo):
        mock_repo.create.return_value = Note(
            id=3,
            title="No Tags",
            content="body",
            tags=[],
            created_at=datetime(2026, 1, 1, 12, 0, 0),
        )

        response = client.post(
            "/notes",
            json={
                "title": "No Tags",
                "content": "body",
            },
        )

        assert response.status_code == 201
        assert response.json()["tags"] == []


class TestCreateNoteValidation:

    # missing title → 422
    def test_create_note_missing_title_returns_422(self, client: TestClient):
        response = client.post(
            "/notes",
            json={
                "content": "no title here",
            },
        )

        assert response.status_code == 422

    # empty string title violates min_length=1 → 422
    def test_create_note_empty_title_returns_422(self, client: TestClient):
        response = client.post(
            "/notes",
            json={
                "title": "",
                "content": "something",
            },
        )

        assert response.status_code == 422

    # title over 100 chars violates max_length → 422
    def test_create_note_title_too_long_returns_422(self, client: TestClient):
        response = client.post(
            "/notes",
            json={
                "title": "a" * 101,
                "content": "something",
            },
        )

        assert response.status_code == 422

    # empty JSON body → 422
    def test_create_note_empty_body_returns_422(self, client: TestClient):
        response = client.post("/notes", json={})

        assert response.status_code == 422

    # malformed JSON → 422
    def test_create_note_invalid_json_returns_422(self, client: TestClient):
        response = client.post(
            "/notes",
            content=b"not json at all",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422


class TestCreateNoteIdempotency:

    # same key twice → cached result, repo called only once
    def test_duplicate_idempotency_key_returns_cached(
        self, client: TestClient, mock_repo
    ):
        headers = {"idempotency-key": "unique-key-1"}
        payload = {
            "title": "Test Note",
            "content": "Some content",
            "tags": ["tag1"],
        }

        first = client.post("/notes", json=payload, headers=headers)
        second = client.post("/notes", json=payload, headers=headers)

        assert first.status_code == 201
        assert second.status_code == 201
        assert first.json() == second.json()
        mock_repo.create.assert_awaited_once()

    # different keys → each triggers a separate create
    def test_different_idempotency_keys_create_separately(
        self, client: TestClient, mock_repo
    ):
        payload = {
            "title": "Test Note",
            "content": "Some content",
            "tags": ["tag1"],
        }

        client.post("/notes", json=payload, headers={"idempotency-key": "key-a"})
        client.post("/notes", json=payload, headers={"idempotency-key": "key-b"})

        assert mock_repo.create.await_count == 2

    # no header → note is created normally
    def test_no_idempotency_key_still_works(self, client: TestClient, mock_repo):
        response = client.post(
            "/notes",
            json={
                "title": "Test Note",
                "content": "Some content",
                "tags": ["tag1"],
            },
        )

        assert response.status_code == 201
        mock_repo.create.assert_awaited_once()


class TestCreateAndRetrieveNote:

    # create a note then fetch it by id via GET /notes/{id}
    def test_create_then_get_by_id(self, client: TestClient, mock_repo):
        created_note = Note(
            id=1,
            title="Test Note",
            content="Some content",
            tags=["tag1"],
            created_at=datetime(2026, 1, 1, 12, 0, 0),
        )
        mock_repo.create.return_value = created_note
        mock_repo.get.return_value = created_note

        # create
        create_resp = client.post(
            "/notes",
            json={
                "title": "Test Note",
                "content": "Some content",
                "tags": ["tag1"],
            },
        )
        assert create_resp.status_code == 201
        created = create_resp.json()

        # retrieve by id
        get_resp = client.get(f"/notes/{created['id']}")
        assert get_resp.status_code == 200

        fetched = get_resp.json()
        assert fetched["id"] == created["id"]
        assert fetched["title"] == created["title"]
        assert fetched["content"] == created["content"]
        assert fetched["tags"] == created["tags"]

    # GET /notes/{id} for a non-existent note → 404
    def test_get_nonexistent_note_returns_404(self, client: TestClient, mock_repo):
        mock_repo.get.return_value = None

        response = client.get("/notes/999")

        assert response.status_code == 404
