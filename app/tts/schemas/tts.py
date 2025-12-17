from pydantic import BaseModel, Field

from app.tts.config import settings


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=settings.TTS_MAX_TEXT_LEN)
    voice: str | None = "default"
    format: str | None = settings.TTS_DEFAULT_FORMAT
