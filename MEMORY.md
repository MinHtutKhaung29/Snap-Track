# MEMORY.md

## What This App Does
Snap-Track: a spending tracker where you type or photograph a payment in one chat thread and get a confirmed record. The AI files expenses, income, bills and installments; you ask questions in plain language and the answers are computed in SQL.

## Done So Far
- 2026-11-23: Added `AGENTS.md`, `.agents/` guard hooks, `MEMORY.md`, `DECISIONS.md`, `.gitignore`.
- 2026-11-24: Read all school documents, wrote `docs/base-plan.md` (v3), `docs/implementation-plan.md`, `docs/p005-technical-validation.md`.
- 2026-11-24: **P0 base** — MySQL 8.4.9, 8 tables applied twice cleanly, 9 categories seeded, `/health` ok. Branch `feat/p1-auth`.
- 2026-11-24: **P1 chat spine** — sentence → tool call → row → undo, behind a server-side confirm gate. Login scaffold behind `app/shared/auth.py`.
- 2026-11-24: Gemini wiring proven live (key as `?key=`, `.env` wins, retries on timeouts).
- 2026-11-25: **P2 receipts** — swipe queue, single-state receipt UI, any payment evidence accepted, camera inside the composer pill.
- 2026-11-25: **P3 commitments** — due-day clamping (31 → month end), installments that sum exactly, 毎月の支払い restored on the due row.
- 2026-11-25: **M4 UI foundation** — shell rebuilt from studied source, light by default with dark on system preference, split stylesheets, recipient read from transfer screenshots. Contrast sweep passes; hardcoded hex only inside palette blocks.
- 2026-11-25: Handoff claims re-checked, two chat bugs fixed: the greeting card now leaves on the first message, and reply bubbles carry a clock time without a reload.

## Verification Today (2026-11-25)
- `.verify` chat journey 12/12 — `documents/_extract/verify/20261125T100750Z-chat`
- Suites green: `test_gate` 15/15, `test_confirm` 15/15, `test_extract` 6/6, `test_commitments` OK, `smoke_auth` 10/10, `ui_instant` 8/8, `ui_image_forms` 11/11
- `documents/_extract/theme/contrast.py` — ALL CHECKS PASS
- Photo → record proven: ¥3,200, 東京電力エナジーパートナー, category 5, `source_kind=photo`

## Next Steps
- Monthly summary surface (queue item 3, needs owner go-ahead).
- Owner review of the dark surface captures (queue item 4).
- Commitment cards (`_commitment_msg.html`) never show a clock time — same treatment as chat bubbles.
- Server for the demo runs on 127.0.0.1:8010, no reload: a Python change only takes effect after the owner restarts it.
