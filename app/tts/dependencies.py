from app.tts.config import settings
from app.tts.services.synthesizer import (
    BaseSynthesizer,
    DummySynthesizer,
    OpenAISynthesizer,
    OpenAIVoice,
    SynthesizerOptions,
)


def get_synthesizer() -> BaseSynthesizer:
    if settings.TTS_PROVIDER == "openai":
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is required when TTS_PROVIDER=openai")
        return OpenAISynthesizer(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_TTS_MODEL,
            voice=OpenAIVoice(settings.OPENAI_TTS_VOICE),
        )
    return DummySynthesizer(
        options=SynthesizerOptions(sample_rate=settings.TTS_SAMPLE_RATE)
    )
