from app.gateway.config import settings
from app.gateway.services.orchestrator import Orchestrator


def get_orchestrator() -> Orchestrator:
    return Orchestrator(settings.TTS_URL)
