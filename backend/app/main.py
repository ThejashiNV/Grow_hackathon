import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.changes import router as changes_router
from app.api.routes.health import router as health_router
from app.api.routes.stocks import router as stocks_router
from app.core.chroma_client import connect_chroma
from app.core.config import get_settings
from app.core.database import close_mongo, connect_mongo
from app.core.redis_client import close_redis, connect_redis

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_mongo()
    await connect_redis()
    connect_chroma()
    logger.info("Startup complete")
    yield
    await close_mongo()
    await close_redis()


settings = get_settings()

app = FastAPI(title="Smart Market Watchlist API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(stocks_router, prefix="/api")
app.include_router(changes_router, prefix="/api")


@app.get("/")
async def root() -> dict:
    return {"name": "Smart Market Watchlist API", "docs": "/docs"}
