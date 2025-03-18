from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class MessageBase(BaseModel):
    content: str
    timestamp: datetime = datetime.now()
    is_user: bool
    username: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: str
    avatar: Optional[str] = None

    class Config:
        orm_mode = True

class ChatResponse(BaseModel):
    id: str
    content: str
    timestamp: datetime
    is_user: bool = False
    username: str = "AI Assistant"
    avatar: Optional[str] = None

class TypingStatus(BaseModel):
    client_id: str
    is_typing: bool

class FileUpload(BaseModel):
    filename: str
    content_type: str
    size: int
