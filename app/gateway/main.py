from fastapi import FastAPI
from app.gateway.api.ws import router as ws_router
from app.gateway.api.health import router as health_router
from app.gateway.api.sessions import router as sessions_router
from app.gateway.api.turns import router as turns_router

app = FastAPI()
app.include_router(ws_router)
app.include_router(health_router)
app.include_router(sessions_router)
app.include_router(turns_router)