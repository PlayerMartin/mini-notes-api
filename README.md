# Mini Notes API
Complete implementation of the Mini Notes API assessment.

## Developer Notes
This solution separates files similarly to layered architecture 
for simplicity. This might not be the *Pythonist* way. However,
that's what I'm the most comfortable with.

For simplicity the .env file is version controlled, of course
it would be in .gitignore in production software.

## How to Run
Prerequisites:
- [Docker](https://www.docker.com/)

Start the stack from the repository root:
```bash
docker compose up --build
```

Services:
- API: http://localhost:8080
- OpenAPI docs: http://localhost:8080/docs

Stop the stack:
```bash
docker compose down
```

## Project Structure
`backend/` contains the FastAPI application and tests:
- `main.py`: FastAPI app entry point and router registration.
- `controllers/`: request/response routing for notes and webhook endpoints.
- `models/`: Pydantic schemas for notes and webhook payloads.
- `repositories/`: data access layer (notes storage, webhook log).
- `config/`: dependency injection setup and database config.
- `tests/`: pytest suites for notes and webhook flows.

## Run Tests
From the repository root:
```bash
cd backend
uv sync --dev
uv run pytest
```

## Curl Commands

### Create a note
```bash
curl -X POST http://localhost:8080/notes \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy milk","content":"2L","tags":["shopping"]}'
```

### List notes
```bash
curl http://localhost:8080/notes
```

### Search notes
```bash
curl "http://localhost:8080/notes?q=milk"
```

### Filter by tag
```bash
curl "http://localhost:8080/notes?tag=shopping"
```

### Webhook with token
```bash
curl -X POST http://localhost:8080/webhooks/note \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Token: note-webhook" \
  -d '{"source":"n8n","message":"Reminder: submit timesheet","tags":["admin"]}'
```
