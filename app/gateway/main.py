from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.gateway.api.ws import router as ws_router
from app.gateway.api.health import router as health_router
from app.gateway.api.sessions import router as sessions_router
from app.gateway.api.turns import router as turns_router
from app.gateway.api.characters import router as characters_router
from app.shared.logging import setup_logging, get_logger
from app.gateway.config import settings

# Initialize structured logging
setup_logging(json_format=settings.LOG_JSON)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("gateway_started", port=8000)
    yield
    logger.info("gateway_shutdown")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_router)
app.include_router(health_router)
app.include_router(sessions_router)
app.include_router(turns_router)
app.include_router(characters_router)