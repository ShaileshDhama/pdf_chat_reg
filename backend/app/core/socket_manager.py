from fastapi import WebSocket
from typing import Dict, List
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.typing_status: Dict[str, bool] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.typing_status[client_id] = False

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.typing_status:
            del self.typing_status[client_id]

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

    async def broadcast(self, message: dict, exclude: str = None):
        for client_id, connection in self.active_connections.items():
            if client_id != exclude:
                await connection.send_json(message)

    async def update_typing_status(self, client_id: str, is_typing: bool):
        self.typing_status[client_id] = is_typing
        status_message = {
            "type": "typing_status",
            "client_id": client_id,
            "is_typing": is_typing
        }
        await self.broadcast(status_message, exclude=client_id)

manager = ConnectionManager()
