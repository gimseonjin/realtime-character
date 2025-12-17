import io
import math
import struct
import wave
from abc import ABC, abstractmethod
from dataclasses import dataclass


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
    def synthesize(self, text: str) -> bytes:
        pass


class DummySynthesizer(BaseSynthesizer):
    def __init__(self, options: SynthesizerOptions | None = None):
        self.options = options or SynthesizerOptions()

    def synthesize(self, text: str) -> bytes:
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
