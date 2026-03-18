from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class ChatType(str, Enum):
    PRIVATE = "private"
    GROUP = "group"


class ChatCreate(BaseModel):
    participant_ids: List[int]          # для приватного чата — обычно 2 id (я + собеседник)
    type: ChatType = ChatType.PRIVATE
    name: Optional[str] = None          # только для групп


class ChatParticipantRead(BaseModel):
    user_id: int
    username: str


class ChatRead(BaseModel):
    id: int
    type: ChatType
    name: Optional[str]
    created_at: datetime
    participants: List[ChatParticipantRead]
    last_message: Optional[dict] = None     # можно позже заполнять

    class Config:
        from_attributes = True