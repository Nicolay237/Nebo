from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.chat import Chat, ChatParticipant, ChatType
from src.models.user import User


async def get_or_create_private_chat(
    db: AsyncSession,
    user_id: int,
    other_user_id: int
) -> Chat:
    # Ищем существующий приватный чат между двумя пользователями
    stmt = (
        select(Chat)
        .join(ChatParticipant)
        .where(Chat.type == ChatType.PRIVATE)
        .where(
            ChatParticipant.user_id.in_([user_id, other_user_id])
        )
        .group_by(Chat.id)
        .having(func.count(ChatParticipant.user_id) == 2)
        .options(selectinload(Chat.participants).selectinload(ChatParticipant.user))
    )
    result = await db.execute(stmt)
    chat = result.scalar_one_or_none()

    if chat:
        return chat

    # Создаём новый
    new_chat = Chat(type=ChatType.PRIVATE)
    db.add(new_chat)
    await db.flush()  # получаем id

    participants = [
        ChatParticipant(chat_id=new_chat.id, user_id=user_id),
        ChatParticipant(chat_id=new_chat.id, user_id=other_user_id),
    ]
    db.add_all(participants)
    await db.commit()
    await db.refresh(new_chat, attribute_names=["participants"])

    # подгружаем пользователей
    await db.refresh(new_chat.participants[0].user)
    await db.refresh(new_chat.participants[1].user)

    return new_chat


async def get_user_chats(
    db: AsyncSession,
    user_id: int
) -> list[Chat]:
    stmt = (
        select(Chat)
        .join(ChatParticipant)
        .where(ChatParticipant.user_id == user_id)
        .options(
            selectinload(Chat.participants).selectinload(ChatParticipant.user),
            selectinload(Chat.messages).order_by(Message.created_at.desc()).limit(1)
        )
        .order_by(Chat.id.desc())   # или по последнему сообщению позже
    )
    result = await db.execute(stmt)
    return result.scalars().all()