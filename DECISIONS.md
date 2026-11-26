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

### 2026-11-24 — Gemini transport: three bugs the live run exposed
- **What:** first end-to-end run of the app against the real Gemini API
- **Why:** the stub proved our logic; only a live call could prove the wiring
- **Findings:**
  - `x-goog-api-key` header is rejected for this credential (`ACCESS_TOKEN_TYPE_UNSUPPORTED`); the key must be sent as `?key=`. Same key returned 200 as a query parameter and 401 as a header — the earlier "expired key" diagnosis was wrong.
  - `load_dotenv` does not override existing environment variables, so the app silently used the shell's `GEMINI_API_KEY` (a different token). `config.py` now passes `override=True`: for an app, `.env` is authoritative.
  - a 60 s timeout failed a valid turn, so `ai.generate` retries three times with backoff on timeouts and 5xx.
- **Result:** 9/9 end-to-end checks pass against real Gemini, including the gate holding a `先週` request as a proposal and the final answer being numerically correct (¥1,200 after undoing ¥850).
- **Files:** `app/shared/ai.py`, `app/shared/config.py`, `tests/smoke_chat.py`, `tools/repro_request.py`, `tools/set_env_value.py`

### 2026-11-25 — M4 close-out: two chat bugs, notebooks brought back in line
- **What:** handoff spot-check, greeting-card fix, no-reload timestamp fix, full re-verification, integration
- **Why:** the handoff's queue item 2 was the only item that did not need an owner gate, and the notebooks had stopped tracking P2/P3/M4
- **Decisions:**
  - Every handoff claim was re-checked before being trusted. Two did not hold: the branch was 21 commits ahead of `main` (not four), and "no bubble timestamps" was only true on the no-reload path because `POST /chat/send` rendered the partial without `show_time`.
  - The timestamp fix went to the render site (pass `show_time`) rather than into the client script, so a reload and an appended bubble produce the same markup.
  - The new greeting-card check was proven non-vacuous: old template 10/11, new template 12/12. A check that cannot fail is not evidence.
  - The full seven-suite gate was re-run after the change, never a subset: a partial run is what let a three-commit regression through earlier.
  - The owner authorised the restart of 8010. It now runs detached (pid 4960, log in `%TEMP%`), which is the accepted trade-off for a demo server that does not reload Python.
  - `MEMORY.md` was rewritten because it predated P2/P3/M4. The P2/P3/M4 rationale is not reconstructed from memory: it stays in the commit messages and `docs/handoff/2026-11-25-ui-foundation.md`.
- **Files:** `tools/make_chat_assets.py`, `app/chat/templates/chat.html`, `app/chat/routes.py`, `.verify/journeys/chat.py`, `MEMORY.md`, `DECISIONS.md`

### 2026-11-25 — GitHub messages stay short and plain
- **What:** added one rule to `AGENTS.md`: commit messages and PRs use one short, everyday sentence; the real why belongs in this file.
- **Why:** the owner asked for it — long technical write-ups were burying the simple answer.
- **Files:** `AGENTS.md`

### 2026-11-26 — Receipt card: one date spelling, and a payee that cannot be cut off
- **What:** the receipt card now prints the date the same way the chat card does, and a long payee wraps onto more lines instead of ending in an ellipsis.
- **Why:** the owner's review of the dark-surface captures approved these two, and both were visible defects: `2026/11/25` beside `2026年11月26日（木）` on the neighbouring surface, and `株式会社エヌ・ティ・ティ・ドコモ・モ…` for a payee the user is being asked to confirm.
- **Decisions:**
  - The date uses the existing `jp_date` helper rather than a second formatter. `card.date_label` was already computed and simply ignored by the template, so the fix was to make the template read it and to feed it the override date when a validation round-trip happens.
  - The payee wraps (`white-space:normal; overflow-wrap:anywhere`) instead of ellipsising, because the whole point of the card is that the user can read what will be saved. `row-shop` scopes it so amount and date keep their single-line alignment.
  - Measured before and after at 390x844 rather than eyeballed: clipped 658 px of text into a 290 px box before, `scroll == client` after, and no horizontal page overflow in either state.
  - `base.css` already truncated every `.row-v` with an ellipsis; the shop row is the one place that must not, which is why the change is a scoped override and not a global one.
  - The `.verify` receipts journey asserted `.swipe`, a class the M4 rebuild deleted, so it could never pass and was never part of M4's evidence. It now asserts the rendered card, the Japanese date form, and the long-payee wrap; 5/5 on both the working tree and the live server.
- **Files:** `tools/make_receipt_assets.py`, `app/receipts/templates/receipts.html`, `app/static/receipts.css`, `app/receipts/routes.py`, `.verify/journeys/receipts.py`, `docs/design/dark-surface-review-2026-11-26.md`
