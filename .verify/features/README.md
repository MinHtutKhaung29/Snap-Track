# Feature map — Snap & Track

One file per user-facing surface. Read the file before driving; a proof that drives one convenient entry point is incomplete when this map lists others.

| surface | file | covers |
|---|---|---|
| Chat (home) | [chat.md](chat.md) | typing a sentence, the confirmation gate, undo, questions |
| Receipts | [receipts.md](receipts.md) | photo upload, swipe card, fix state, discard, queue |
| Login | [login.md](login.md) | register, login, logout, rejected credentials |

Not yet built, so not mapped: bills and installments (P3), standing facts and history search (P4).

Conventions used by every file:
- Runner: `python ~/.agents/skills/verify-web-app/scripts/verify.py <surface> --project .` (the global `verify-web-app` skill owns launch, doctor, evidence and cleanup)
- Contract: `.verify/config.json`; journeys: `.verify/journeys/<surface>.py`; driver: Playwright from the project venv
- Viewport: 390x844, `is_mobile`, `locale="ja-JP"`
- Evidence: `documents/_extract/verify/<stamp>-<surface>/` (`shots/`, `video/`, `report.json`, `console.log`)
- Show the evidence to the human: `verify.py serve --no-launch --project .` prints a URL for them
- One throwaway user per run (`verify-<epoch>-<surface>@example.com`); `verify.py cleanup` removes their rows and never deletes evidence.
- Always read the database back; a screenshot alone cannot prove money was recorded.
