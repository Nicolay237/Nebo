from sqlalchemy.ext.asyncio import AsyncSession

from src.models.message import Message


async def create_message(
    db: AsyncSession,
    chat_id: int,
    sender_id: int,
    content: str
) -> Message:
    msg = Message(
        chat_id=chat_id,
        sender_id=sender_id,
        content=content,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg