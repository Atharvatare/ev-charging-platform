from typing import List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Keeps track of all currently connected WebSocket client channels
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accepts a incoming WebSocket handshake and tracks the client channel."""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket Client Connected: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        """Removes a client channel from active broadcasts list."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"WebSocket Client Disconnected: {websocket.client}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Sends a JSON string directly to a target socket."""
        await websocket.send_text(message)

    async def broadcast(self, message: dict):
        """Asynchronously broadcasts telemetry details to all active clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                # Catch closed socket channels dynamically to avoid broadcast blockout
                print(f"Failed to send to client. Removing from pool. Error: {e}")
                self.disconnect(connection)

# Global singleton WebSocket connection manager
manager = ConnectionManager()
