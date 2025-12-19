from pydantic import BaseModel, Field

from app.tts.config import settings
from app.tts.services.synthesizer import OpenAIFormat, OpenAIVoice


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=settings.TTS_MAX_TEXT_LEN)
    voice: OpenAIVoice = OpenAIVoice.ALLOY
    format: OpenAIFormat = OpenAIFormat.WAV
