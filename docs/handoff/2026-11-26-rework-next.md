# Handoff — rework after the phone review, next phase

Date: 2026-11-26
Previous phase: `docs/handoff/2026-11-26-phone-test.md` (phone acceptance pass)

## Mission anchor (verbatim; do not paraphrase)

- Goal: A Japanese graduation project — a spending tracker where the user types or photographs a payment in chat and gets a confirmed record.
- Master plan: `docs/base-plan.md`
- Docs / links: `docs/design/chat-ui-spec.md` · `docs/handoff/2026-11-25-m4-close.md` · `docs/test-walkthrough.md` · `docs/design/ui-review-2026-11-26.md` · `docs/design/ui-sweep-findings-2026-11-26.md` · `docs/design/ai-native-latency-2026-11-26.md` · `docs/design/base-color-and-font-2026-11-26.md` · `docs/intent/2026-11-26_phone-rework.md` · `MEMORY.md` · `DECISIONS.md`
- Current milestone: M4 — every surface (chat, receipts, commitments) passes its suite, renders correctly in light and dark at 390x844, and a photographed payment screenshot becomes a persisted record carrying amount, date and recipient. Status: met, merged as `a235733`; the owner then ran his own phone review and opened this rework round.
- Non-goals / hard constraints: no monthly-summary work; no 住居費 category without a `docs/base-plan.md` amendment; **no hardcoded parsing of money phrases** (owner rejected it explicitly — the AI must understand); no push or merge to `main` without the owner's word; leave the stray process on port 8011 alone.

## Teaching state (owner-facing)

- Latency in plain words: the wait is the remote model thinking, and the old 60s timeout + retry turned one stall into a two-minute hang. Thinking off plus a 10s timeout took the worst case from 124s to ~17s. Depth: `docs/design/ai-native-latency-2026-11-26.md`.
- Why a swipe alone is not enough: WCAG 2.5.7 requires a non-drag path, so tap buttons and arrow keys stay beside the gesture. Depth: `docs/design/ui-review-2026-11-26.md` §2.
- Why the teal is not just `#4F7075`: white on it passes AA (5.37:1), but the same hex as text on the dark background fails (3.32:1), so dark mode uses `#7FA6AC`. Depth: `docs/design/base-color-and-font-2026-11-26.md`.
- Arial has no kana, so the stack pins Japanese fallbacks instead of letting each OS guess.

## What this phase changed (all uncommitted)

- Send control: icon-only 44×44 arrow outside the input pill, grey and disabled when empty.
- One swipe component for every yes/no surface: ask card and proposal card share markup, gesture, pending state, buttons, arrow keys. Proposal save still posts to `/chat/confirm/<id>`; the model never approves money.
- `ask_user` tool + `question` payload + `POST /chat/answer/<id>`: a binary question arrives as a card; the answer is stored as a normal user message and continues the same turn.
- Latency: `GEMINI_THINKING=off` default, `GEMINI_TIMEOUT=10`, per-attempt log lines (`ai_attempt …`), per-turn timings in `service.LAST_TIMINGS`, `settle_record()` extracted. Bench: `tools/bench_turn.py`.
- Design: accent `#4F7075` (dark text tint `#7FA6AC`), Arial + Japanese fallback stack, focus halo instead of an accent border, inline SVG favicon, `レシート` tab renamed `写真`, 「日付は推測です」 suppressed when the date is today.
- Test tooling: `tests/ui_send.py` (composer + real send), `tests/ui_perf.py` (frames + endpoint ms), `tests/ui_sweep.py` (10-step click sweep, ~15s, headed or headless).

## Evidence from this phase

- Fast sweep: 10/10 steps, 0 console errors, 0 failed requests; frames p50 16.7ms, p95 16.9–24.1ms, max 34.7ms — `documents/_extract/ui-sweep/report-fast.json`.
- Latency bench: p50 1.0–3.0s model time, worst 17.5s, versus 69.6–123.6s tails before.
- Suites: `test_ask` 38/38, `test_gate` 15/15, `test_confirm` 15/15, `test_commitments` 16 OK, `test_extract` 6/6.
- Screenshots: `documents/_extract/ui-send/`, `documents/_extract/ui-sweep/`.

## Environment state

- App runs from this checkout on `127.0.0.1:8010` (uvicorn without `--reload`; restart after Python edits).
- Port 8011 still holds an older instance — untouched, owner decision pending.
- No Cloudflare tunnel is open (owner asked for it closed); the public URL now returns 530.
- Tests create throwaway users (`sweep-…`, `live-watch-…`, `bench@example.com`) and real rows in the local DB.

## What is left (owner-ordered, one at a time)

1. **The owner's third phone finding** — named 2026-11-26: the photo may be the **thing he bought** (clothes, water bottle, snack, juice), not a receipt; he sends the picture and the price he paid, and when the price is missing the app must ask. Answered in this round.
2. **Trim the proposal card** — it still shows title + amount + category + source + full date + hint + two buttons + 直す + time. Agreed: amount/category/source on one line, date only when not today, hint once and muted, buttons kept for accessibility, 直す as a text link.
3. **Streaming decision** — not built. Both frontier lanes said measure first; per-stage timing now exists. Streaming only helps text turns, never the tool-call wait, and partial amounts must never render as money.
4. **Untested surfaces** — photo/camera upload via the file chooser, commitments buttons beyond the single one present, keyboard-only use, real touchscreen swipe, error states (AI timeout, quota, invalid amount).

## Next actions

1. Ask the owner for the third phone finding, in his words, before writing any code. Done — see `docs/design/item-photo-and-card-trim-2026-11-26.md`.
2. If none is coming: trim the proposal card exactly as specified above and capture `ui_sweep` before/after at 390×740 and 1280×800.
3. After any change run `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tests/ui_sweep.py` plus the five suites; do not claim green without the output.
4. Restart uvicorn on 8010 after Python edits; bring the browser window to the foreground before any live demo or the owner sees nothing.
5. Commit only when the owner asks; nothing is pushed and `main` is still `a235733`.

## Open questions for the owner

- Is `#4F7075` accent only, or also the page background? The spec assumes accent.
- Dark mode: keep `#7FA6AC` for accent text, or accept `#4F7075` at 3.32:1?
- Do the tabs stay チャット / 写真 / 支払い予定, or does he want different words?
- Does the third phone item change the order of items 2–4?
