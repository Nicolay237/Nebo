from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.database import get_db
from src.api.deps import current_user
from src.models.user import User
from src.crud.chat import get_or_create_private_chat, get_user_chats
from src.schemas.chat import ChatCreate, ChatRead, ChatType


router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("/", response_model=ChatRead)
async def create_chat(
    chat_data: ChatCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user)
):
    if chat_data.type == ChatType.PRIVATE:
        if len(chat_data.participant_ids) != 1:
            raise HTTPException(400, "Для приватного чата нужен ровно один собеседник")

        other_id = chat_data.participant_ids[0]
        if other_id == user.id:
            raise HTTPException(400, "Нельзя создать чат с самим собой")

        chat = await get_or_create_private_chat(db, user.id, other_id)
        return chat

    else:
        # Групповой чат — пока заглушка (можно реализовать позже)
        raise HTTPException(501, "Групповые чаты пока не поддерживаются")


@router.get("/", response_model=List[ChatRead])
async def get_my_chats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user)
):
    chats = await get_user_chats(db, user.id)
    return chats