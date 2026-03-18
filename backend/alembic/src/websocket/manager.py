from fastapi import WebSocket
from typing import Dict, List


class ConnectionManager:
    def __init__(self):
        # chat_id → список подключённых WebSocket
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, chat_id: int):
        await websocket.accept()
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = []
        self.active_connections[chat_id].append(websocket)

    async def disconnect(self, websocket: WebSocket, chat_id: int):
        connections = self.active_connections.get(chat_id, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections:
            self.active_connections.pop(chat_id, None)

    async def broadcast(self, chat_id: int, message: dict):
        if chat_id in self.active_connections:
            for connection in self.active_connections[chat_id][:]:  # копия списка
                try:
                    await connection.send_json(message)
                except Exception:
                    # можно удалить сломанный сокет
                    await self.disconnect(connection, chat_id)