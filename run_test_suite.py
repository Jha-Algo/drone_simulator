import asyncio
import threading
import time
import urllib.request
import json
import uvicorn
import websockets
from main import app

TEST_PORT = 8765
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"
WS_BASE_URL = f"ws://127.0.0.1:{TEST_PORT}"

class ServerThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.config = uvicorn.Config(app, host="127.0.0.1", port=TEST_PORT, log_level="warning")
        self.server = uvicorn.Server(self.config)
        self.daemon = True

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True

async def run_suite():
    print(f"=== Starting Drone Simulator Test Suite on {BASE_URL} ===")
    server_thread = ServerThread()
    server_thread.start()
    
    # Wait for server to be responsive
    for _ in range(20):
        try:
            req = urllib.request.urlopen(f"{BASE_URL}/health", timeout=1)
            if req.status == 200:
                print("Server is up and healthy.")
                break
        except Exception:
            time.sleep(0.2)
    else:
        raise RuntimeError("Server failed to start within timeout")

    try:
        # 1. Test GET /
        print("\n[TEST 1] GET / (3D Simulator Frontend)")
        req = urllib.request.urlopen(f"{BASE_URL}/")
        assert req.status == 200
        html = req.read().decode('utf-8')
        assert "AI DRONE SIMULATOR" in html, "Missing Simulator title"
        assert "qrcode-container" in html, "Missing QR Code element"
        assert "DynamicRibbonTrail" in html, "Missing Wingtip ribbon trail"
        assert "TorusGeometry" in html, "Missing checkpoint rings geometry"
        assert "flight-crosshair" in html, "Missing flight reticle"
        print("  --> PASS: Simulator HTML contains 3D Drone, HUD, QR Code & Wingtip Trails.")

        # 2. Test GET /room/ABCD
        print("\n[TEST 2] GET /room/ABCD (Room parameter routing)")
        req = urllib.request.urlopen(f"{BASE_URL}/room/ABCD")
        assert req.status == 200
        print("  --> PASS: Room URL /room/ABCD returned 200.")

        # 3. Test GET /controller/ABCD
        print("\n[TEST 3] GET /controller/ABCD (Mobile Controller Frontend)")
        req = urllib.request.urlopen(f"{BASE_URL}/controller/ABCD")
        assert req.status == 200
        ctrl_html = req.read().decode('utf-8')
        assert "AI AUTO-PILOT" in ctrl_html, "Missing Autopilot button"
        assert "zone-left" in ctrl_html and "zone-right" in ctrl_html, "Missing dual joystick zones"
        assert "nipplejs" in ctrl_html, "Missing NippleJS joystick library"
        print("  --> PASS: Mobile controller contains dual joysticks & AI Autopilot toggle.")

        # 4. Test GET /controller (Fallback query param)
        print("\n[TEST 4] GET /controller")
        req = urllib.request.urlopen(f"{BASE_URL}/controller")
        assert req.status == 200
        print("  --> PASS: /controller endpoint returned 200.")

        # 5. Test WebSockets: Full Room Pairing & Input Relay
        print("\n[TEST 5] Real-Time WebSocket Room Pairing & Control Relay")
        room_id = "FLY1"
        sim_ws_url = f"{WS_BASE_URL}/ws/{room_id}/simulator"
        ctrl_ws_url = f"{WS_BASE_URL}/ws/{room_id}/controller"

        async with websockets.connect(sim_ws_url) as sim_ws:
            # 1. Simulator initial status
            msg1 = await sim_ws.recv()
            data1 = json.loads(msg1)
            print("  --> Simulator connected. Initial status:", data1)
            assert data1["type"] == "controller_status"
            assert data1["connected"] is False

            # 2. Mobile controller connects
            async with websockets.connect(ctrl_ws_url) as ctrl_ws:
                msg2 = await ctrl_ws.recv()
                data2 = json.loads(msg2)
                print("  --> Controller connected. Received simulator status:", data2)
                assert data2["type"] == "simulator_status"
                assert data2["connected"] is True

                # Simulator receives pairing alert
                msg3 = await sim_ws.recv()
                data3 = json.loads(msg3)
                print("  --> Simulator received mobile connection alert:", data3)
                assert data3["type"] == "controller_status"
                assert data3["connected"] is True

                # 3. Transmit real-time joystick control inputs from phone
                control_packet = {
                    "type": "control",
                    "throttle": 0.85,
                    "yaw": -0.4,
                    "pitch": 0.7,
                    "roll": 0.2,
                    "autopilot": True
                }
                await ctrl_ws.send(json.dumps(control_packet))

                # Simulator receives forwarded input
                relayed_msg = await sim_ws.recv()
                relayed_data = json.loads(relayed_msg)
                print("  --> Simulator received forwarded control packet:", relayed_data)
                assert relayed_data["throttle"] == 0.85
                assert relayed_data["autopilot"] is True
                assert relayed_data["pitch"] == 0.7

            # After controller disconnects, simulator is notified
            msg4 = await sim_ws.recv()
            data4 = json.loads(msg4)
            print("  --> Controller disconnected. Simulator received status:", data4)
            assert data4["type"] == "controller_status"
            assert data4["connected"] is False

        print("\n=======================================================")
        print(">>> ALL 5 TEST SUITES PASSED PERFECTLY! <<<")
        print("=======================================================")

    finally:
        server_thread.stop()

if __name__ == "__main__":
    asyncio.run(run_suite())
