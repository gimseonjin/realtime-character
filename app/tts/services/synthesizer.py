import io
import math
import struct
import wave
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

import httpx


class OpenAIVoice(str, Enum):
    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    NOVA = "nova"
    SHIMMER = "shimmer"


class OpenAIFormat(str, Enum):
    MP3 = "mp3"
    OPUS = "opus"
    AAC = "aac"
    FLAC = "flac"
    WAV = "wav"
    PCM = "pcm"


@dataclass
class SynthesizeOptions:
    """Options for a single synthesize call."""

    voice: OpenAIVoice = OpenAIVoice.ALLOY
    format: OpenAIFormat = OpenAIFormat.WAV


class SynthesizerError(Exception):
    """Base exception for synthesizer errors."""

    pass


@dataclass
class SynthesizerOptions:
    sample_rate: int = 24000
    tone_hz: int = 440
    ms_per_char: int = 35
    min_ms: int = 180
    max_ms: int = 1600
    volume: float = 0.25


class BaseSynthesizer(ABC):
    @abstractmethod
    def synthesize(self, text: str, options: SynthesizeOptions | None = None) -> bytes:
        pass

# 테스트용 더미 구현
class DummySynthesizer(BaseSynthesizer):
    def __init__(self, options: SynthesizerOptions | None = None):
        self.options = options or SynthesizerOptions()

    def synthesize(self, text: str, options: SynthesizeOptions | None = None) -> bytes:
        opt = self.options
        # 텍스트 길이에 따라 음성 길이를 대충 맞춰서 "chunk가 따라오는 느낌"을 준다
        dur_ms = max(opt.min_ms, min(opt.max_ms, len(text) * opt.ms_per_char))
        duration_sec = dur_ms / 1000.0

        n_channels = 1
        sampwidth = 2  # 16-bit
        framerate = opt.sample_rate
        n_frames = int(duration_sec * framerate)

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(n_channels)
            wf.setsampwidth(sampwidth)
            wf.setframerate(framerate)

            # 간단한 사인파 톤 생성(PCM16)
            for i in range(n_frames):
                t = i / framerate
                sample = opt.volume * math.sin(2 * math.pi * opt.tone_hz * t)
                pcm = int(max(-1.0, min(1.0, sample)) * 32767)
                wf.writeframes(struct.pack("<h", pcm))

        return buf.getvalue()


class OpenAISynthesizer(BaseSynthesizer):
    OPENAI_TTS_URL = "https://api.openai.com/v1/audio/speech"

    def __init__(self, api_key: str, model: str = "tts-1", voice: OpenAIVoice = OpenAIVoice.ALLOY):
        if not api_key:
            raise ValueError("OpenAI API key is required")
        self.api_key = api_key
        self.model = model
        self.default_voice = voice

    def synthesize(self, text: str, options: SynthesizeOptions | None = None) -> bytes:
        opts = options or SynthesizeOptions(voice=self.default_voice)

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.OPENAI_TTS_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "input": text,
                        "voice": opts.voice.value,
                        "response_format": opts.format.value,
                    },
                )
                response.raise_for_status()
                return response.content
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise SynthesizerError("Invalid OpenAI API key") from e
            elif e.response.status_code == 429:
                raise SynthesizerError("OpenAI rate limit exceeded") from e
            else:
                raise SynthesizerError(f"OpenAI API error: {e.response.status_code}") from e
        except httpx.TimeoutException as e:
            raise SynthesizerError("OpenAI API timeout") from e
        except httpx.RequestError as e:
            raise SynthesizerError(f"Network error: {e}") from e
