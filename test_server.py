import asyncio
import json
import os
import sys
import urllib.request
import websockets

PORT = int(os.environ.get("PORT", 8000))
BASE_URL = f"http://127.0.0.1:{PORT}"
WS_BASE_URL = f"ws://127.0.0.1:{PORT}"

async def run_tests():
    print(f"--- Running Automated Drone Simulator Verification against {BASE_URL} ---")
    
    # 1. Test GET /
    print("1. Testing GET / (Simulator page)...")
    req = urllib.request.urlopen(f"{BASE_URL}/")
    assert req.status == 200, f"Expected 200, got {req.status}"
    content = req.read().decode('utf-8')
    assert "AI DRONE SIMULATOR" in content, "Missing HUD brand title"
    assert "qrcode-container" in content, "Missing QR code container"
    assert "DynamicRibbonTrail" in content, "Missing ribbon trail implementation"
    assert "three.min.js" in content, "Missing Three.js script inclusion"
    print("   [PASS] GET / returned 200 OK and valid 3D Simulator HTML structure.")

    # 2. Test GET /room/TEST
    print("2. Testing GET /room/TEST...")
    req = urllib.request.urlopen(f"{BASE_URL}/room/TEST")
    assert req.status == 200, f"Expected 200, got {req.status}"
    print("   [PASS] GET /room/TEST returned 200 OK.")

    # 3. Test GET /controller/TEST
    print("3. Testing GET /controller/TEST (Mobile Controller page)...")
    req = urllib.request.urlopen(f"{BASE_URL}/controller/TEST")
    assert req.status == 200, f"Expected 200, got {req.status}"
    controller_html = req.read().decode('utf-8')
    assert "AI AUTO-PILOT" in controller_html, "Missing Autopilot button"
    assert "zone-left" in controller_html and "zone-right" in controller_html, "Missing dual joystick zones"
    assert "nipplejs" in controller_html, "Missing nipplejs reference"
    print("   [PASS] GET /controller/TEST returned 200 OK and valid Mobile Controller HTML.")

    # 4. Test GET /health
    print("4. Testing GET /health...")
    req = urllib.request.urlopen(f"{BASE_URL}/health")
    assert req.status == 200
    health_json = json.loads(req.read().decode('utf-8'))
    assert health_json.get("status") == "ok"
    print(f"   [PASS] Health check OK: {health_json}")

    # 5. Test WebSockets: Real-time room relay
    print("5. Testing WebSocket real-time connection and control relay...")
    room_id = "ABCD"
    sim_ws_url = f"{WS_BASE_URL}/ws/{room_id}/simulator"
    ctrl_ws_url = f"{WS_BASE_URL}/ws/{room_id}/controller"

    async with websockets.connect(sim_ws_url) as sim_ws:
        init_sim_msg = await sim_ws.recv()
        sim_data = json.loads(init_sim_msg)
        print(f"   Simulator received initial status: {sim_data}")
        assert sim_data.get("type") == "controller_status"
        assert sim_data.get("connected") is False

        # Connect mobile controller
        async with websockets.connect(ctrl_ws_url) as ctrl_ws:
            ctrl_init_msg = await ctrl_ws.recv()
            ctrl_data = json.loads(ctrl_init_msg)
            print(f"   Controller received initial status: {ctrl_data}")
            assert ctrl_data.get("type") == "simulator_status"
            assert ctrl_data.get("connected") is True

            # Simulator should now receive notification that controller is connected
            sim_notify_msg = await sim_ws.recv()
            sim_notify = json.loads(sim_notify_msg)
            print(f"   Simulator received controller connected notification: {sim_notify}")
            assert sim_notify.get("type") == "controller_status"
            assert sim_notify.get("connected") is True

            # Send test control input from mobile
            test_control = {
                "type": "control",
                "throttle": 0.75,
                "yaw": -0.25,
                "pitch": 0.60,
                "roll": -0.10,
                "autopilot": True
            }
            await ctrl_ws.send(json.dumps(test_control))

            # Simulator should receive the forwarded control input
            relayed_msg = await sim_ws.recv()
            relayed_data = json.loads(relayed_msg)
            print(f"   Simulator successfully received relayed control: {relayed_data}")
            assert relayed_data.get("throttle") == 0.75
            assert relayed_data.get("autopilot") is True
            assert relayed_data.get("pitch") == 0.60

        # After controller closes, simulator should receive disconnected notification
        disconnect_msg = await sim_ws.recv()
        disconnect_data = json.loads(disconnect_msg)
        print(f"   Simulator received controller disconnect notification: {disconnect_data}")
        assert disconnect_data.get("type") == "controller_status"
        assert disconnect_data.get("connected") is False

    print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<\n")

if __name__ == "__main__":
    asyncio.run(run_tests())
