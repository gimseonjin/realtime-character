from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.tts.schemas.tts import TTSRequest
from app.tts.dependencies import get_synthesizer
from app.tts.services.synthesizer import (
    BaseSynthesizer,
    OpenAIFormat,
    SynthesizeOptions,
)

router = APIRouter()

CONTENT_TYPES = {
    OpenAIFormat.WAV: "audio/wav",
    OpenAIFormat.MP3: "audio/mpeg",
    OpenAIFormat.OPUS: "audio/opus",
    OpenAIFormat.AAC: "audio/aac",
    OpenAIFormat.FLAC: "audio/flac",
    OpenAIFormat.PCM: "audio/pcm",
}


@router.post("/tts")
def tts(
    req: TTSRequest,
    synthesizer: BaseSynthesizer = Depends(get_synthesizer),
):
    options = SynthesizeOptions(voice=req.voice, format=req.format)
    audio = synthesizer.synthesize(req.text, options)
    media_type = CONTENT_TYPES.get(req.format, "audio/wav")
    return Response(content=audio, media_type=media_type)
