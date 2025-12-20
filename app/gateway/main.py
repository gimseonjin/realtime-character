from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.gateway.api.ws import router as ws_router
from app.gateway.api.health import router as health_router
from app.gateway.api.sessions import router as sessions_router
from app.gateway.api.turns import router as turns_router
from app.gateway.api.characters import router as characters_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_router)
app.include_router(health_router)
app.include_router(sessions_router)
app.include_router(turns_router)
app.include_router(characters_router)