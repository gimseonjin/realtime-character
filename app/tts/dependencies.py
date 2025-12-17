from app.tts.config import settings
from app.tts.services.synthesizer import BaseSynthesizer, DummySynthesizer, SynthesizerOptions


def get_synthesizer() -> BaseSynthesizer:
    return DummySynthesizer(
        options=SynthesizerOptions(sample_rate=settings.TTS_SAMPLE_RATE)
    )
