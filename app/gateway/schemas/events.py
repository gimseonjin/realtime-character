from typing import Literal
from pydantic import BaseModel


class TokenEvent(BaseModel):
    type: Literal["token"] = "token"
    text: str


class AudioChunkEvent(BaseModel):
    type: Literal["audio_chunk"] = "audio_chunk"
    seq: int
    format: str
    data: str  # base64 encoded


class DoneEvent(BaseModel):
    type: Literal["done"] = "done"


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    message: str
