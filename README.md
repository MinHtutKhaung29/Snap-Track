# Snap & Track

Photograph a receipt, or just say what you spent, and the AI files it. Then ask your own money questions in plain language and get answers computed from your real data.

Mobile-first web app · Python 3.13 · FastAPI · Jinja2 · MySQL 8.4 · Gemini `gemini-3.1-flash-lite`

## What exists today

Phase P0 (the base). The app boots, connects to MySQL, and reports its own health. Login, chat and receipts arrive in P1–P2.

- `GET /health` — JSON: MySQL version, database, table count, pinned model
- `GET /` — status page rendered from live data
- `GET /docs` — FastAPI's generated API documentation

## Setup from a fresh terminal

Requirements: Windows, Git, Python 3.13 (`py -3.13`), and MySQL 8.4 installed but **not** necessarily configured.

```powershell
git clone https://github.com/MinHtutKhaung29/Snap-Track.git
cd Snap-Track
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**1. Start MySQL once** (data directory lives under your profile, so no admin rights are needed):

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\mysql-data" | Out-Null
& "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqld.exe" --initialize-insecure --basedir="C:\Program Files\MySQL\MySQL Server 8.4" --datadir="$env:USERPROFILE\mysql-data"
Start-Process -FilePath "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqld.exe" -ArgumentList '--basedir="C:\Program Files\MySQL\MySQL Server 8.4" --datadir="' + $env:USERPROFILE + '\mysql-data" --port=3306 --bind-address=127.0.0.1 --default-time-zone=+09:00 --character-set-server=utf8mb4' -WindowStyle Hidden
```

Only the first two lines are once-ever; the third line starts the server each time.

**2. Create the database, the app user and `.env`:**

```powershell
.\.venv\Scripts\python.exe db\provision.py
```

**3. Apply the schema and seed the categories:**

```powershell
.\.venv\Scripts\python.exe db\install.py
```

Safe to run twice — it only creates what is missing.

**4. Run the app:**

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

Open <http://127.0.0.1:8010/health>. Expected:

```json
{"version":"8.4.9","db":"snapandtrack","tables":8,"status":"ok","model":"gemini-3.1-flash-lite"}
```

## Documents

- `docs/base-plan.md` — the specification: product, scope, 8-table schema, AI safety rule, security, phases
- `docs/implementation-plan.md` — task-level plan for P0–P2
- `docs/p005-technical-validation.md` — the measured 技術検証: receipt reading and tool selection

## Rules of this repo

Read `AGENTS.md` first. `main` is protected: work on a `feat/<name>` branch and open a pull request. Never commit `.env`, `documents/` or `uploads/`.
