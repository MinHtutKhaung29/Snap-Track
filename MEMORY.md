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
- 2026-11-26: **M4 review follow-up** — receipt date prints as `2026年11月25日（水）` like the chat card, and a long payee wraps instead of being cut off with `…`. The review also found the receipts journey asserting a class M4 deleted (`.swipe`), so that suite had been passing nothing; it is fixed and now 5/5.

## Verification Today (2026-11-26)
- `receipts` journey 5/5 on the live server (8010) and on a working-tree instance (8021) — `documents/_extract/verify/20261126T014956Z-receipts`
- `ui_image_forms` 11/11 · `test_extract` 6/6 · `contrast.py` ALL CHECKS PASS
- Long payee measured at 390x844: 658 px of text in a 290 px box before, no clipping after, no page overflow
- Theme captures regenerated from the working tree: `documents/_extract/theme/*.png`; pre-fix sets kept in `prior-20261125T1559/` and `prior-20261126T1035/`

## Next Steps
- Owner restarts 8010 when convenient — the date/override change is Python and only takes effect after a restart; templates and CSS are already live.
- A stray instance is listening on 8011 (old code, not started by this session) and will confuse future verification; it needs an owner decision, not a silent kill.
- Monthly summary surface (needs owner go-ahead on chat answer vs card).
- Handoff claim "commitment cards never show a clock time" is wrong: `_commitment_msg.html` renders `show_time` and `app/chat/routes.py` passes it. Re-check before spending a session on it.
