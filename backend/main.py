import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.exceptions import RequestValidationError
from starlette.responses import PlainTextResponse

from controllers.note_controller import router as note_router
from controllers.webhook_controller import router as webhook_router

load_dotenv()

app = FastAPI()
app.include_router(note_router)
app.include_router(webhook_router)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8080)
