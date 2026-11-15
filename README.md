# 🚁 3D AI Drone Simulator - Public Sharing & Website Embedding Guide

Is application ko aap **4 aasan tareeqo** se kisi ko bhi bhej sakte hain aur kisi bhi website par chala sakte hain:

---

## ⚡ Method 1: Instant 1-Click Public Link (Sabse Aasan - No Setup)

Agar aapko turant kisi dost ya client ko link bhejna hai:
1. Workspace me **`share_online.bat`** file par double-click karein (ya terminal me run karein):
   ```bash
   python share_online.py
   ```
2. Yeh automatic ek **Free Secure Public HTTPS Link** generate karega (jaise `https://xxxx.trycloudflare.com`).
3. **Yeh link kisi ko bhi bhej dein!**
   - Wo apne laptop browser me yeh link kholega.
   - Apne mobile phone se QR code scan karega.
   - Duniya me kahi se bhi (mobile data / Wi-Fi) real-time drone fly kar sakega!

---

## 🌐 Method 2: Embed in Any Website (WordPress, Wix, React, HTML)

Agar aapke paas koi website hai aur aap simulator ko us website ke andar chalana chahte hain:

### Single Line Iframe Code:
```html
<!-- 3D Drone Simulator Embed -->
<iframe 
  src="https://YOUR-PUBLIC-URL/simulator.html" 
  width="100%" 
  height="650px" 
  frameborder="0" 
  allow="accelerometer; gyroscope; fullscreen" 
  allowfullscreen>
</iframe>
```

- **WordPress / Elementor:** Page editor me "Custom HTML" widget add karein aur yeh code paste karein.
- **Wix / Squarespace:** "Embed Code / HTML iframe" component add karein.
- **React / Next.js / Vue:** Normal `<iframe>` component me render karein.
- **Live Demo:** Browser me [http://localhost:8000/embed](http://localhost:8000/embed) open karke live preview dekhein.

---

## 🚀 Method 3: 100% Free Cloud Deployment (Render / Railway)

Permanent 24/7 public link ke liye (jaise `https://my-drone-sim.onrender.com`):

1. Is folder ko apne **GitHub** account par push karein:
   ```bash
   git init
   git add .
   git commit -m "3D Drone Simulator"
   git remote add origin https://github.com/<YOUR-USERNAME>/<REPO-NAME>.git
   git push -u origin main
   ```
2. **[Render.com](https://render.com)** par login karein (Free account).
3. "New +" par click karein -> **Web Service** choose karein.
4. Apna GitHub repo select karein:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. "Create Web Service" par click karein! 2 minute me aapki permanent public live website ready ho jayegi.

---

## 📦 Method 4: Serverless / GitHub Pages / Static Web Hosting

Is project me **Dual-Mode Communication (WebSocket + WebRTC PeerJS)** built-in hai:
- Agar aap bina kisi backend/Python server ke sirf files ko **GitHub Pages**, **Netlify**, ya **Vercel** par host karte hain:
- Yeh automatic **WebRTC P2P (PeerJS)** mode me switch ho jata hai!
- Laptop aur phone direct peer-to-peer connect ho jaate hain bina kisi server cost ke!

---

## 🎮 Localhost Testing (Apne Computer Par)

- **Simulator:** [http://localhost:8000/](http://localhost:8000/)
- **Mobile Controller:** [http://localhost:8000/controller/DEMO](http://localhost:8000/controller/DEMO)
- **Embed Preview:** [http://localhost:8000/embed](http://localhost:8000/embed)
