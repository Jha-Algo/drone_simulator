import subprocess
import time
import re
import sys
import os
import urllib.request
import webbrowser

PORT = 8000
CLOUDFLARED_EXE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cloudflared.exe")

def is_server_running():
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=1)
        return req.status == 200
    except Exception:
        return False

def main():
    print("=" * 65)
    print("   🚁 3D AI DRONE SIMULATOR - INSTANT PUBLIC SHARING TOOL   ")
    print("=" * 65)

    # 1. Start backend server if not running
    if not is_server_running():
        print("[1/2] Starting local Drone Simulator backend on port 8000...")
        subprocess.Popen([sys.executable, "main.py"], creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
        for _ in range(15):
            if is_server_running():
                print("      Local server is up and running!")
                break
            time.sleep(0.5)
        else:
            print("ERROR: Failed to start local server on port 8000.")
            return
    else:
        print("[1/2] Local Drone Simulator server is already running on port 8000.")

    # 2. Check cloudflared.exe
    if not os.path.exists(CLOUDFLARED_EXE):
        print(f"ERROR: {CLOUDFLARED_EXE} not found.")
        return

    print("\n[2/2] Generating free public HTTPS tunnel via Cloudflare...")
    print("      (No account, password, or setup needed. Works worldwide!)\n")

    cmd = [CLOUDFLARED_EXE, "tunnel", "--url", f"http://127.0.0.1:{PORT}"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")

    public_url = None
    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    # Read output until public URL is spotted
    for line in iter(proc.stdout.readline, ''):
        match = url_pattern.search(line)
        if match:
            public_url = match.group(0)
            break
        if "error" in line.lower() and "failed" in line.lower():
            print(line.strip())

    if not public_url:
        print("ERROR: Could not obtain public Cloudflare URL.")
        return

    print("=" * 65)
    print("       🎉 YOUR SIMULATOR IS NOW LIVE WORLDWIDE! 🎉")
    print("=" * 65)
    print(f"\n👉 PUBLIC SIMULATOR URL (Share this with anyone):")
    print(f"   {public_url}\n")
    print(f"📱 MOBILE CONTROLLER TEST LINK:")
    print(f"   {public_url}/controller/DEMO\n")
    print("=" * 65)
    print("• Kisi ko bhi yeh link bhej sakte hain (WhatsApp, Telegram, etc.)!")
    print("• Wo apne laptop par link kholega, aur apne mobile se QR code scan")
    print("  karke drone control kar sakega (chahe wo kisi bhi internet/Wi-Fi par ho)!")
    print("• Tunnel band karne ke liye is window ko band karein ya CTRL+C dabayein.")
    print("=" * 65)

    # Try copying to clipboard
    try:
        import tkinter as tk
        r = tk.Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(public_url)
        r.update()
        r.destroy()
        print("\n✅ Link copied to your clipboard!")
    except Exception:
        pass

    # Open in browser
    try:
        webbrowser.open(public_url)
    except Exception:
        pass

    # Keep tunnel alive
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down public tunnel...")
        proc.terminate()

if __name__ == "__main__":
    main()
