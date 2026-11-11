# Naina — Deployment Guide

This guide covers: local dev setup, production server hosting, Tailscale private
tunnel, auto-start on Windows boot, and how every LLM connection works.

---

## Architecture Overview

```
[Browser / Phone]
       |
   Tailscale VPN (private 100.x.x.x)  OR  Cloudflare tunnel (public HTTPS)
       |
  FastAPI server  (naina/api/routes.py)   — port 8000
       |
  Agent Loop  (naina/agent/loop.py)
       |
  ┌────────────────┐
  │  Ollama (local)│  <-- tries first (llama3.2:3b on your machine)
  └────────────────┘
       | fails / timeout
  ┌────────────────┐
  │  Groq (cloud)  │  <-- auto-fallback (llama-3.3-70b, free tier)
  └────────────────┘
```

---

## 1. Local Development (first time setup)

### Prerequisites

```bash
# Python 3.11+
pip install -r requirements.txt

# Ollama (local LLM)
# Download from https://ollama.com
ollama pull llama3.2:3b
```

### Run

```bash
python run.py
```

Opens browser at `http://localhost:8000` automatically.

---

## 2. How LLM Connection Works

### Flow (brain.py)

1. On startup, Naina checks if Ollama is running at `http://localhost:11434`
2. If Ollama is up and the model is loaded → **uses Ollama** (offline, fast, private)
3. If Ollama times out or errors → **falls back to Groq** (cloud, faster for complex tasks)
4. If both fail → returns a setup instructions message

### Config (naina/config.py) — things you must set

| Key | Default | What to do |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Change if Ollama runs on another machine |
| `OLLAMA_MODEL` | `llama3.2:3b` | Change to any model you have pulled (e.g. `mistral`, `llama3.1:8b`) |
| `OLLAMA_TIMEOUT` | `8` seconds | Increase if your machine is slow |
| `GROQ_API_KEY` | `""` | **Get free key at console.groq.com — paste here** |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq free tier supports this model |

### Pull a different Ollama model

```bash
ollama pull mistral          # 7B, good balance
ollama pull llama3.1:8b      # smarter, needs ~8GB RAM
ollama pull phi3:mini        # very fast, small RAM
```

Then update `OLLAMA_MODEL` in `config.py`.

### Use Groq only (no local LLM)

Set `OLLAMA_TIMEOUT = 0` in `config.py` — Ollama check will fail instantly and
Groq will always be used. Get your free API key at **console.groq.com**.

---

## 3. Host on Your Server (LAN or VPS)

### Bind to all interfaces

`config.py` already has:
```python
FASTAPI_HOST = "0.0.0.0"
FASTAPI_PORT = 8000
```

This means the server is reachable on all network interfaces as soon as it starts.

### Access from another device on LAN

```
http://<your-pc-local-ip>:8000
```

Find your local IP: `ipconfig` on Windows → look for `IPv4 Address` under your
Wi-Fi or Ethernet adapter (e.g. `192.168.1.x`).

### VPS / cloud server

1. Copy the project to the server (`git clone` or `scp`)
2. Install dependencies: `pip install -r requirements.txt`
3. Set `GROQ_API_KEY` in `config.py` (Ollama won't run on most VPS free tiers)
4. Run with systemd (Linux):

```bash
# /etc/systemd/system/naina.service
[Unit]
Description=Naina AI Assistant
After=network.target

[Service]
User=youruser
WorkingDirectory=/home/youruser/NAINA
ExecStart=/usr/bin/python3 run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable naina
sudo systemctl start naina
```

---

## 4. Tailscale Private Tunnel (Recommended)

Tailscale creates a **WireGuard VPN mesh** between your devices.
No port forwarding, no public exposure, works behind NAT/CGNAT.

### Setup (one time)

1. Download Tailscale: **https://tailscale.com/download**
2. Install on your **PC** (where Naina runs) and your **phone/laptop**
3. Sign in with the same account on both devices
4. Done — both devices get a stable `100.x.x.x` IP

### On the Naina PC

```bash
# Check your Tailscale IP
tailscale ip -4
# Output: 100.x.x.x
```

Naina detects this automatically on startup and logs:
```
Tailscale active — private URL: http://100.x.x.x:8000
```

### Access from phone or laptop

Open: `http://100.x.x.x:8000` (use the IP from the log above)

This works from **anywhere in the world** as long as both devices are online and
connected to Tailscale — coffee shop, mobile data, different country.

### Tailscale vs Cloudflare tunnel

| Feature | Tailscale | Cloudflare tunnel |
|---|---|---|
| Privacy | Private (only your devices) | Public HTTPS URL |
| Speed | Direct WireGuard (very fast) | Proxied through Cloudflare |
| Auth required | Yes — must be on your Tailscale | No |
| Persistent URL | Yes (same IP always) | Random URL each restart |
| Use case | Personal access | Sharing with others |

Both run simultaneously — Tailscale for your private access, Cloudflare when you
want to share a temporary link.

---

## 5. Auto-Start on Windows Boot

### What already works

`main.py` calls `_register_startup()` on every run — this writes to:
```
HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run
```
Key: `Naina` → `"python.exe" "path\to\run.py"`

This means Naina starts **when you log in to Windows**.

### To verify it's registered

```
Win + R → regedit
Navigate to: HKCU\Software\Microsoft\Windows\CurrentVersion\Run
Look for "Naina" key
```

### For startup BEFORE login (as a Windows Service)

Use NSSM (Non-Sucking Service Manager):

```bash
# Download nssm from https://nssm.cc/download
nssm install Naina "C:\path\to\python.exe" "C:\path\to\NAINA\run.py"
nssm set Naina AppDirectory "C:\path\to\NAINA"
nssm start Naina
```

This starts Naina as a Windows Service — runs at boot even before any user logs in.

### Tailscale starts automatically

Tailscale installs as a Windows Service by default — it starts at boot before login.
By the time you log in (and Naina starts), Tailscale is already connected and the
`100.x.x.x` IP is active.

### Boot sequence (full picture)

```
PC Powers On
    ↓
Windows starts Tailscale service → 100.x.x.x IP assigned
    ↓
User logs in
    ↓
Windows Run key fires → python run.py starts
    ↓
Naina FastAPI starts on port 8000
    ↓
Naina detects Tailscale IP → logs private URL
    ↓
Naina starts Cloudflare tunnel → logs public HTTPS URL
    ↓
Browser opens http://localhost:8000
    ↓
TTS: "Namaste Shivay! Naina ready hai."
```

---

## 6. Developer Checklist

These are the things **you must configure** before Naina works properly:

- [ ] **Groq API key** — get free key at `console.groq.com`, paste in `config.py` → `GROQ_API_KEY`
- [ ] **Ollama** — install from `ollama.com`, run `ollama pull llama3.2:3b`
- [ ] **Tailscale** — install on PC + phone, sign in with same account
- [ ] **Music folder** — set `MUSIC_DIR` in `config.py` to your actual music path
- [ ] **User name** — set `USER_NAME` in `config.py` (default: "Shivay")
- [ ] **Weather** — get free key at `openweathermap.org`, paste in `OPENWEATHER_KEY`
- [ ] **News** — get free key at `newsapi.org`, paste in `NEWSAPI_KEY`

### Optional / advanced

- [ ] **Cloudflare tunnel** — install `cloudflared` CLI from Cloudflare's site for public HTTPS URL
- [ ] **Google Calendar** — OAuth2 token setup (see `config.py` → `GOOGLE_CAL_TOKEN`)
- [ ] **Phone ADB** — enable Developer Options + Wireless ADB on Android, set `PHONE_IP`
- [ ] **Push notifications** — set `NTFY_TOPIC` in `config.py`, install `ntfy` app on phone

---

## 7. Ports Reference

| Port | Service | Accessible from |
|---|---|---|
| `8000` | Naina FastAPI | localhost + LAN + Tailscale |
| `11434` | Ollama | localhost only |
| `5555` | Android ADB (wireless) | LAN only |

---

## 8. Checking Status

Visit `http://localhost:8000/api/ai/status` to see if Ollama and Groq are reachable:

```json
{
  "ollama": { "reachable": true, "model_loaded": true, "model": "llama3.2:3b" },
  "groq":   { "configured": true, "reachable": true, "model": "llama-3.3-70b-versatile" }
}
```
