from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json

router = APIRouter(prefix="/ws", tags=["collaboration"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, project_id: str, websocket: WebSocket):
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)

    def disconnect(self, project_id: str, websocket: WebSocket):
        if project_id in self.active_connections:
            if websocket in self.active_connections[project_id]:
                self.active_connections[project_id].remove(websocket)
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]

    async def broadcast(self, project_id: str, message: str, sender: WebSocket):
        if project_id in self.active_connections:
            for connection in self.active_connections[project_id]:
                if connection != sender:
                    try:
                        await connection.send_text(message)
                    except Exception:
                        pass

manager = ConnectionManager()

@router.websocket("/projects/{project_id}")
async def project_websocket_endpoint(websocket: WebSocket, project_id: str):
    await manager.connect(project_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(project_id, data, websocket)
    except WebSocketDisconnect:
        manager.disconnect(project_id, websocket)
