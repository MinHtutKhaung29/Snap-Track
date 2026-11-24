# MEMORY.md

## What This App Does
Snap-Track: an app that tracks your money by taking a photo or by talking to one chat thread. The AI files expenses, income, bills and installments; you ask questions in plain language and the answers are computed in SQL.

## Done So Far
- 2026-11-23: Added `AGENTS.md`, `.agents/` guard hooks, `MEMORY.md`, `DECISIONS.md`, and `.gitignore`.
- 2026-11-24: Read all school documents and wrote the base specification (`docs/base-plan.md` v3), a task-level plan (`docs/implementation-plan.md`) and the measured 技術検証 (`docs/p005-technical-validation.md`).
- 2026-11-24: **P0 base is running.** MySQL 8.4.9 installed, database + app user provisioned, 8 tables applied twice without error, 9 categories seeded in UTF-8. FastAPI app boots; `/health` returns `{"status":"ok","tables":8}`.
- 2026-11-24: Repo cloned into this folder with real history; `documents/`, `uploads/`, `.env`, `.venv/` are gitignored. Work is on branch `feat/p0-base`.

## Next Steps
- P1 chat spine: **done and tested 9/9** — sentence → tool call → row → undo. Gate proven: 「先週の金曜 ランチ 1200円」 writes nothing until confirmed.
- **Blocker for real AI:** the Gemini key currently in `.env` is an ephemeral access token that expired. A real `AIza...` key from aistudio.google.com/apikey is needed before the live path works. Tests run with `AI_MODE=stub` in the meantime.
- P2 photo + swipe card, P3 commitments, P4 ask & remember.
- Commit P1 on `feat/p1-auth` and push after PR #1 merges; do not merge without the owner.
