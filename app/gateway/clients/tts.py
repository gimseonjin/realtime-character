import httpx


class TTSClient:
    def __init__(self, base_url: str, voice: str = "alloy"):
        self.base_url = base_url.rstrip("/")
        self.voice = voice

    async def synthesize(self, text: str, fmt: str = "wav") -> bytes:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{self.base_url}/tts",
                json={"text": text, "format": fmt, "voice": self.voice},
            )
            r.raise_for_status()
            return r.content
