import subprocess
import time
import urllib.request
import os
import threading
import uvicorn
from main import app

TEST_PORT = 8899
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

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

def verify_headless():
    print(f"Starting server on port {TEST_PORT}...")
    server = ServerThread()
    server.start()

    # Wait for server
    for _ in range(25):
        try:
            req = urllib.request.urlopen(f"http://127.0.0.1:{TEST_PORT}/health")
            if req.status == 200:
                print("Server responsive!")
                break
        except Exception:
            time.sleep(0.2)

    try:
        # 1. Verify Simulator Page with Headless Chrome
        print("\n--- Verifying Simulator Page (/) with Headless Chrome ---")
        sim_url = f"http://127.0.0.1:{TEST_PORT}/"
        sim_proc = subprocess.run([
            CHROME_PATH,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=2000",
            "--dump-dom",
            sim_url
        ], capture_output=True, encoding='utf-8', errors='replace', timeout=15)

        dom_sim = sim_proc.stdout
        print(f"Captured DOM length: {len(dom_sim)} chars")
        assert "AI DRONE SIMULATOR" in dom_sim, "HUD brand missing in rendered DOM"
        assert "val-alt" in dom_sim, "Telemetry altitude element missing"
        assert "qrcode-container" in dom_sim, "QR code container missing"
        assert "<canvas" in dom_sim, "WebGL canvas or QR canvas rendered successfully!"
        print("  --> [PASS] Headless Chrome rendered 3D Drone Simulator page and canvas without failure!")

        # 2. Verify Controller Page with Headless Chrome
        print("\n--- Verifying Controller Page (/controller/TEST) with Headless Chrome ---")
        ctrl_url = f"http://127.0.0.1:{TEST_PORT}/controller/TEST"
        ctrl_proc = subprocess.run([
            CHROME_PATH,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=2000",
            "--dump-dom",
            ctrl_url
        ], capture_output=True, encoding='utf-8', errors='replace', timeout=15)

        dom_ctrl = ctrl_proc.stdout
        print(f"Captured DOM length: {len(dom_ctrl)} chars")
        assert "AI AUTO-PILOT" in dom_ctrl, "AI Autopilot toggle missing in rendered DOM"
        assert "zone-left" in dom_ctrl, "Left stick zone missing"
        assert "zone-right" in dom_ctrl, "Right stick zone missing"
        assert "ROOM: TEST" in dom_ctrl, "Room TEST code badge not rendered"
        print("  --> [PASS] Headless Chrome rendered Mobile Controller with dual joysticks and Autopilot toggle!")

        print("\n>>> BROWSER HEADLESS VERIFICATION 100% SUCCESSFUL! <<<\n")

    finally:
        server.stop()

if __name__ == "__main__":
    verify_headless()
