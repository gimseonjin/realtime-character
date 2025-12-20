from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.tts.api.http import router as http_router
from app.tts.api.health import router as health_router
from app.shared.logging import setup_logging, get_logger
from app.tts.config import settings

setup_logging(json_format=settings.LOG_JSON)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("tts_started", port=8001)
    yield
    logger.info("tts_shutdown")


app = FastAPI(title="tts-service", lifespan=lifespan)
app.include_router(http_router)
app.include_router(health_router)