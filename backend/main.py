import yaml
import asyncio
import json
from pathlib import Path
from typing import List
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .schemas import AppConfig, SystemMetrics
from .manager import SystemDataManager

# Global manager instance (will be properly initialized in lifespan)
manager: SystemDataManager = None

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, metrics: SystemMetrics):
        """Broadcast metrics to all connected clients."""
        if not self.active_connections:
            return
            
        message = metrics.model_dump_json()
        # Create a copy to avoid modification during iteration
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)

connection_manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global manager
    # Startup: load config and start background task
    config = load_config()
    manager = SystemDataManager(buffer_size=config.core.buffer_size)
    # Register the broadcast callback
    manager.broadcast_callback = connection_manager.broadcast
    manager.start(interval=config.core.interval)
    yield
    # Shutdown: stop background task
    if manager:
        manager.stop()

app = FastAPI(title="Linux System Monitor API", lifespan=lifespan)

# Define frontend path
frontend_dir = Path(__file__).parent.parent / "frontend"

@app.get("/")
async def get_index():
    return FileResponse(frontend_dir / "index.html")

def load_config() -> AppConfig:
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)
    return AppConfig(**config_data)

@app.get("/api/config", response_model=AppConfig)
async def get_config():
    return load_config()

@app.websocket("/ws/metrics")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)
    try:
        # Step 2: Push history on connection
        history = manager.get_history()
        history_data = [m.model_dump() for m in history]
        await websocket.send_text(json.dumps(history_data))
        
        # Keep the connection open and listen for messages (if any)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception:
        connection_manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    config = load_config()
    uvicorn.run(app, host=config.core.host, port=config.core.port)
