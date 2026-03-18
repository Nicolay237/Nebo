from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from src.websocket.manager import ConnectionManager
from src.api.deps import current_user  # ← теперь используем нормальную зависимость
from src.models.user import User
from src.database import get_db
from src.crud.message import create_message
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/ws/chat/{chat_id}")
async def websocket_chat(
    websocket: WebSocket,
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),   # ← работает с JWT!
):
    await manager.connect(websocket, chat_id)

    try:
        await websocket.send_json({
            "type": "system",
            "content": f"Добро пожаловать в чат #{chat_id}"
        })

        while True:
            data = await websocket.receive_json()

            if data.get("type") == "message":
                content = data.get("content", "").strip()
                if not content:
                    continue

                # Сохраняем в БД
                msg = await create_message(db, chat_id, user.id, content)

                # Формируем ответ
                broadcast_msg = {
                    "type": "message",
                    "id": msg.id,
                    "chat_id": chat_id,
                    "sender_id": user.id,
                    "sender_username": user.username,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                    "is_read": msg.is_read
                }

                await manager.broadcast(chat_id, broadcast_msg)

    except WebSocketDisconnect:
        await manager.disconnect(websocket, chat_id)
        await manager.broadcast(chat_id, {
            "type": "system",
            "content": f"{user.username} покинул чат"
        })