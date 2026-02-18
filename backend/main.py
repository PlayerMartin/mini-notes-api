from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

from config.di import register_singletons

load_dotenv()

from config.db_config import create_db
from controllers.note_controller import router as note_router
from controllers.webhook_controller import router as webhook_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    register_singletons(app)
    await create_db()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(note_router)
app.include_router(webhook_router)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8080)
