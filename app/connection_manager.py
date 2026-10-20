from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()

        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        
        self.active_connections[room_id].append(websocket)

    def disconnection(self, websocket: WebSocket, room_id: str):
        connections = self.active_connections.get(room_id)

        if connections and websocket in connections:
            connections.remove(websocket)

            if not connections:
                del self.active_connections[room_id]
    
    async def broadcast(self, message: str, room_id: str):
        connections = self.active_connections.get(room_id, [])

        for connection in connections.copy():
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnection(connection, room_id)

