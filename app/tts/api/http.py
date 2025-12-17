from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response

from app.tts.schemas.tts import TTSRequest
from app.tts.dependencies import get_synthesizer
from app.tts.services.synthesizer import BaseSynthesizer

router = APIRouter()


@router.post("/tts")
def tts(
    req: TTSRequest,
    synthesizer: BaseSynthesizer = Depends(get_synthesizer),
):
    if (req.format or "").lower() != "wav":
        raise HTTPException(status_code=400, detail="Only 'wav' format is supported in MVP")

    audio = synthesizer.synthesize(req.text)

    return Response(content=audio, media_type="audio/wav")
