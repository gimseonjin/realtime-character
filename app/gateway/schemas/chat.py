from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    session_id: str = Field(..., alias="sessionId")
    text: str

    class Config:
        populate_by_name = True
