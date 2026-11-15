import os
import json
import logging
import random
import string
from pathlib import Path
from typing import Dict, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DroneSimulatorServer")

BASE_DIR = Path(__file__).resolve().parent
SIMULATOR_FILE = BASE_DIR / "simulator.html"
CONTROLLER_FILE = BASE_DIR / "controller.html"
EMBED_FILE = BASE_DIR / "embed.html"

app = FastAPI(
    title="3D AI Drone Simulator",
    description="Web-based 3D Drone Simulator with Real-Time Mobile Touch Remote Controller",
    version="1.0.0"
)

# Enable CORS for flexible deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory if present
STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

class ConnectionManager:
    def __init__(self):
        # room_id -> {"simulator": WebSocket | None, "controllers": set[WebSocket]}
        self.rooms: Dict[str, Dict] = {}

    def _get_room(self, room_id: str) -> Dict:
        norm_id = room_id.upper().strip()
        if norm_id not in self.rooms:
            self.rooms[norm_id] = {
                "simulator": None,
                "controllers": set()
            }
        return self.rooms[norm_id]

    async def register_simulator(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        norm_id = room_id.upper().strip()
        room = self._get_room(norm_id)
        room["simulator"] = websocket
        logger.info(f"Simulator connected to room [{norm_id}]")
        
        # If controllers are already active, notify simulator
        has_controller = len(room["controllers"]) > 0
        await websocket.send_json({
            "type": "controller_status",
            "connected": has_controller,
            "controller_count": len(room["controllers"])
        })

    def disconnect_simulator(self, room_id: str, websocket: WebSocket):
        norm_id = room_id.upper().strip()
        if norm_id in self.rooms:
            if self.rooms[norm_id]["simulator"] == websocket:
                self.rooms[norm_id]["simulator"] = None
                logger.info(f"Simulator disconnected from room [{norm_id}]")
            # If room is completely empty, clean up
            if self.rooms[norm_id]["simulator"] is None and len(self.rooms[norm_id]["controllers"]) == 0:
                del self.rooms[norm_id]

    async def register_controller(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        norm_id = room_id.upper().strip()
        room = self._get_room(norm_id)
        room["controllers"].add(websocket)
        logger.info(f"Mobile controller connected to room [{norm_id}] (Total: {len(room['controllers'])})")

        # Notify controller about simulator availability
        sim_connected = room["simulator"] is not None
        await websocket.send_json({
            "type": "simulator_status",
            "connected": sim_connected,
            "room_id": norm_id
        })

        # Notify simulator that mobile controller is connected
        if room["simulator"]:
            try:
                await room["simulator"].send_json({
                    "type": "controller_status",
                    "connected": True,
                    "controller_count": len(room["controllers"])
                })
            except Exception as e:
                logger.warning(f"Failed to notify simulator in room [{norm_id}]: {e}")

    async def disconnect_controller(self, room_id: str, websocket: WebSocket):
        norm_id = room_id.upper().strip()
        if norm_id in self.rooms:
            room = self.rooms[norm_id]
            room["controllers"].discard(websocket)
            logger.info(f"Mobile controller disconnected from room [{norm_id}] (Remaining: {len(room['controllers'])})")

            # Notify simulator if all controllers disconnected
            if room["simulator"]:
                try:
                    await room["simulator"].send_json({
                        "type": "controller_status",
                        "connected": len(room["controllers"]) > 0,
                        "controller_count": len(room["controllers"])
                    })
                except Exception as e:
                    logger.warning(f"Failed to notify simulator in room [{norm_id}]: {e}")

            if room["simulator"] is None and len(room["controllers"]) == 0:
                del self.rooms[norm_id]

    async def forward_to_simulator(self, room_id: str, data: str):
        norm_id = room_id.upper().strip()
        if norm_id in self.rooms:
            simulator = self.rooms[norm_id]["simulator"]
            if simulator:
                try:
                    await simulator.send_text(data)
                except Exception as e:
                    logger.warning(f"Error forwarding control to simulator in room [{norm_id}]: {e}")

    async def forward_to_controllers(self, room_id: str, data: str):
        norm_id = room_id.upper().strip()
        if norm_id in self.rooms:
            dead_controllers = set()
            for controller in self.rooms[norm_id]["controllers"]:
                try:
                    await controller.send_text(data)
                except Exception:
                    dead_controllers.add(controller)
            for dc in dead_controllers:
                self.rooms[norm_id]["controllers"].discard(dc)

manager = ConnectionManager()

def generate_random_room_id() -> str:
    # 4-character uppercase alphanumeric without confusing letters like I, O, 1, 0
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choices(chars, k=4))

import socket

def get_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

@app.get("/api/network-ip")
async def network_ip():
    return {"lan_ip": get_lan_ip()}

@app.get("/health")
async def health():
    return {"status": "ok", "active_rooms": len(manager.rooms), "lan_ip": get_lan_ip()}

@app.get("/api/room/new")
async def new_room():
    return {"room_id": generate_random_room_id()}

@app.get("/")
async def get_simulator_root():
    if not SIMULATOR_FILE.exists():
        raise HTTPException(status_code=404, detail="simulator.html not found")
    return FileResponse(SIMULATOR_FILE)

@app.get("/room/{room_id}")
async def get_simulator_room(room_id: str):
    if not SIMULATOR_FILE.exists():
        raise HTTPException(status_code=404, detail="simulator.html not found")
    return FileResponse(SIMULATOR_FILE)

@app.get("/embed")
async def get_embed():
    if not EMBED_FILE.exists():
        raise HTTPException(status_code=404, detail="embed.html not found")
    return FileResponse(EMBED_FILE)

@app.get("/controller")
async def get_controller_query():
    if not CONTROLLER_FILE.exists():
        raise HTTPException(status_code=404, detail="controller.html not found")
    return FileResponse(CONTROLLER_FILE)

@app.get("/controller/{room_id}")
async def get_controller(room_id: str):
    if not CONTROLLER_FILE.exists():
        raise HTTPException(status_code=404, detail="controller.html not found")
    return FileResponse(CONTROLLER_FILE)

@app.websocket("/ws/{room_id}/simulator")
async def websocket_simulator(websocket: WebSocket, room_id: str):
    await manager.register_simulator(room_id, websocket)
    try:
        while True:
            # Handle incoming ping / messages from simulator
            msg = await websocket.receive_text()
            try:
                payload = json.loads(msg)
                if payload.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif payload.get("type") == "telemetry":
                    await manager.forward_to_controllers(room_id, msg)
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect_simulator(room_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error on simulator [{room_id}]: {e}")
        manager.disconnect_simulator(room_id, websocket)

@app.websocket("/ws/{room_id}/controller")
async def websocket_controller(websocket: WebSocket, room_id: str):
    await manager.register_controller(room_id, websocket)
    try:
        while True:
            # Fast raw relay of control payloads to laptop simulator
            data = await websocket.receive_text()
            await manager.forward_to_simulator(room_id, data)
    except WebSocketDisconnect:
        await manager.disconnect_controller(room_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error on controller [{room_id}]: {e}")
        await manager.disconnect_controller(room_id, websocket)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting Drone Simulator Server on 0.0.0.0:{port}...")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
