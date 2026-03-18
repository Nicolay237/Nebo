from sqlalchemy import ForeignKey, String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum as PyEnum
from typing import List

from src.database import Base


class ChatType(str, PyEnum):
    PRIVATE = "private"
    GROUP = "group"


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[ChatType] = mapped_column(Enum(ChatType), nullable=False, default=ChatType.PRIVATE)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)  # только для групп

    # участники
    participants: Mapped[List["ChatParticipant"]] = relationship(
        "ChatParticipant", back_populates="chat", cascade="all, delete-orphan"
    )

    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="chat", cascade="all, delete-orphan"
    )


class ChatParticipant(Base):
    __tablename__ = "chat_participants"

    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)

    chat: Mapped["Chat"] = relationship("Chat", back_populates="participants")
    user: Mapped["User"] = relationship("User")