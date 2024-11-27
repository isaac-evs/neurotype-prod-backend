from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import List
import json

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.api import deps
from app.models.user import User
from app.services.chatbot_service import get_chatbot_response

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, List[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        connections = self.active_connections.get(user_id, [])
        connections.append(websocket)
        self.active_connections[user_id] = connections

    def disconnect(self, user_id: int, websocket: WebSocket):
        connections = self.active_connections.get(user_id, [])
        if websocket in connections:
            connections.remove(websocket)
        if connections:
            self.active_connections[user_id] = connections
        else:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    current_user: User = Depends(deps.get_current_user_websocket),
):
    user_id = current_user.id
    db = SessionLocal()
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message["type"] == "message":
                user_message = message["content"]
                # Process the message and get a response from the chatbot
                response = get_chatbot_response(user_message, current_user, db)
                # Send the response back to the user
                await manager.send_personal_message(
                    json.dumps({"type": "response", "content": response}),
                    websocket
                )
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    finally:
        db.close()
