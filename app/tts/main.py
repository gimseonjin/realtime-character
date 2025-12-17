from fastapi import FastAPI
from app.tts.api.http import router as http_router
from app.tts.api.health import router as health_router

app = FastAPI(title="tts-service")
app.include_router(http_router)
app.include_router(health_router)