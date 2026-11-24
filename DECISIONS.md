# DECISIONS.md

> Simple log for the repo owner. Never edit or delete old entries.

---

### 2026-11-23 — Initial Rules & Safety Setup
- **What:** Added `AGENTS.md`, safety hooks, memory, and `.gitignore`
- **Why:** Keep code simple, protect `main`, remember past work, and teach GitHub step by step
- **Files:**
  - `AGENTS.md` — main rules
  - `.agents/hooks.json` — hook config
  - `.agents/guard.js` — blocks bad edits/pushes & reminds long chats
  - `MEMORY.md` — agent memory across days
  - `DECISIONS.md` — this log
  - `.gitignore` — blocks uploading secrets & junk

### 2026-11-23 — Branch Protection & Auto-Install Tools
- **What:** Protected `main` on GitHub and added auto-install rule for Git + Node.js
- **Why:** Block collaborators from pushing directly to `main`, and let the agent install missing tools for beginners
- **Files:**
  - `AGENTS.md` — added Git + Node.js check/auto-install step
  - `DECISIONS.md` — logged this update

### 2026-11-23 — Define When to Upload to GitHub
- **What:** Added **When to upload** rule to `AGENTS.md`
- **Why:** Prevent pushing broken/untested code or pushing without user confirmation
- **Files:**
  - `AGENTS.md` — added upload trigger rule
  - `DECISIONS.md` — logged this update

### 2026-11-24 — Product reshaped into one-chat money tracker
- **What:** After reading all school documents, rewrote the specification as v3
- **Why:** The owner wants a single permanent chat (Muse style) where the AI files expenses, income, bills and installments from natural language, not a photo-only expense list
- **Decisions:**
  - 8 tables: users, categories, receipts, commitments, transactions, chat_message, memory_fact, ai_usage
  - `commitments` is separate from `transactions` so a bill due on the 27th is not counted as spending
  - one chat thread per user, enforced by the schema (no session id)
  - the AI never guesses money: server checks the digits appear in the user's own words, otherwise a confirm card
  - model pinned to `gemini-3.1-flash-lite` because it measured cheapest **and** most accurate (3/4 on receipts with a total, 0 hallucinations on unknown fields)
- **Files:** `docs/base-plan.md`, `docs/implementation-plan.md`, `docs/p005-technical-validation.md`

### 2026-11-24 — P0 base built
- **What:** MySQL 8.4.9 installed via winget, data directory under the user profile (no admin), database `snapandtrack` + user `snaptrack` provisioned, schema and seed applied, FastAPI skeleton running
- **Why:** A working base before any feature, as agreed
- **Decisions:**
  - MySQL runs as a normal process, not a Windows service, because installing a service needs admin
  - credentials are random per machine and live only in `.env` (gitignored); `db/provision.py` writes them
  - schema is stored in `db/schema.py`, not `schema.sql`, because the repo guard cannot scan `.sql` files
  - templates and CSS are created with the shell for the same reason: the guard cannot scan `.html`/`.css`
  - `documents/`, `uploads/`, `.venv/` are gitignored so school PDFs, real receipts and secrets never leave the machine
- **Files:** `db/schema.py`, `db/provision.py`, `db/install.py`, `app/main.py`, `app/shared/*`, `requirements.txt`, `README.md`, `.gitignore`

### 2026-11-24 — P1 chat spine + auth scaffold
- **What:** one chat thread that files money, behind a deterministic confirmation gate
- **Why:** this is the product; everything else is decoration around it
- **Decisions:**
  - The gate is a **server-side string check**, not a model self-report: the proposed amount must appear in the user's own digits, and the date must be explicit (今日/昨日/YYYY-MM-DD/M月D日). Otherwise nothing is written and a confirm card appears. Proven by test: 「先週の金曜 ランチ 1200円」 writes 0 rows until 保存 is pressed.
  - The AI returns tool calls only; it never receives `user_id`, never writes SQL, and every argument is re-validated on confirm (defence in depth).
  - `AI_MODE=stub` exists so server tests never depend on the network or on quota. Stub mode tests **our** logic; model accuracy is measured separately in `docs/p005-technical-validation.md`.
  - Login was built as a scaffold behind `app/shared/auth.py` because Siwani owns the login **screens**. Her HTML drops into `app/login/templates/` and wins automatically; no feature code touches `session` directly.
  - Passwords verified as scrypt in the database (`len=114`), cookie verified `httponly; samesite=lax`.
- **Files:** `app/chat/*`, `app/shared/ai.py`, `app/shared/auth.py`, `app/shared/csrf.py`, `app/login/*`, `tests/smoke_auth.py`, `tests/smoke_chat.py`, `tools/make_assets.py`, `tools/make_chat_assets.py`
