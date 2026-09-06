import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.ask import router as ask_router
from app.api.routes.attention import router as attention_router
from app.api.routes.changes import router as changes_router
from app.api.routes.demo import router as demo_router
from app.api.routes.health import router as health_router
from app.api.routes.history import router as history_router
from app.api.routes.intelligence import router as intelligence_router
from app.api.routes.state import router as state_router
from app.api.routes.stocks import router as stocks_router
from app.api.routes.watchlist import router as watchlist_router
from app.core.chroma_client import connect_chroma
from app.core.config import get_settings
from app.core.database import close_mongo, connect_mongo
from app.core.redis_client import close_redis, connect_redis
from app.services.refresh_pipeline import start_refresh_loop, stop_refresh_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_mongo()
    await connect_redis()
    connect_chroma()
    await start_refresh_loop()
    logger.info("Startup complete")
    yield
    await stop_refresh_loop()
    await close_mongo()
    await close_redis()


settings = get_settings()

app = FastAPI(title="Smart Market Watchlist API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(stocks_router, prefix="/api")
app.include_router(state_router, prefix="/api")
app.include_router(changes_router, prefix="/api")
app.include_router(watchlist_router, prefix="/api")
app.include_router(attention_router, prefix="/api")
app.include_router(ask_router, prefix="/api")
app.include_router(demo_router, prefix="/api")
app.include_router(history_router, prefix="/api")
app.include_router(intelligence_router, prefix="/api")


@app.get("/")
async def root() -> dict:
    return {"name": "Smart Market Watchlist API", "docs": "/docs"}
