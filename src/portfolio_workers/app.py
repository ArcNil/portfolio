from fastapi import FastAPI
from portfolio_workers.database import engine
from contextlib import asynccontextmanager

import portfolio_workers.chats.models as models
from portfolio_workers.chats.routes import router as chat_router
from portfolio_workers.config import get_settings

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.app_env == "dev":
        async with engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan, debug="dev"==settings.app_env)
app.include_router(chat_router)