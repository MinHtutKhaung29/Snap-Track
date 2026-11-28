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
- 2026-11-26: **Merged and handed to the owner for phone testing.** PR #4 merged into `main` (`a235733`), server restarted on the merged code bound to `0.0.0.0:8010`, a scoped firewall rule opened port 8010 to the local subnet, and a Cloudflare quick tunnel published it so a phone on mobile data can use it. Wrote `docs/test-walkthrough.md` from real end-to-end runs (register → chat card → undo → photo → save → bill → dark mode).

## Verification Today (2026-11-26)
- `receipts` journey 5/5 on the live server (8010) and on a working-tree instance (8021) — `documents/_extract/verify/20261126T014956Z-receipts`
- `ui_image_forms` 11/11 · `test_extract` 6/6 · `contrast.py` ALL CHECKS PASS
- Long payee measured at 390x844: 658 px of text in a 290 px box before, no clipping after, no page overflow
- Theme captures regenerated from the working tree: `documents/_extract/theme/*.png`; pre-fix sets kept in `prior-20261125T1559/` and `prior-20261126T1035/`

## Next Steps
- **Owner is mid-test on the Android phone.** Public link: `https://contribute-kinase-afford-riding.trycloudflare.com` (cloudflared quick tunnel to 127.0.0.1:8010). Temporary — restarting it yields a new random name.
- Test script lives in `docs/test-walkthrough.md`; every expected screen there was copied from a real run.
- 2026-11-26: **Owner review rework.** Send button is an icon-only arrow outside the pill; every yes/no surface now uses one swipe card (tap + arrow keys still work); the model can ask a binary question as a card (`ask_user` + `/chat/answer`); Gemini thinking is off by default and the request timeout is 10s, which cut the worst-case turn from 124s to ~17s; base accent is `#4F7075` with an Arial stack and Japanese fallbacks; `/favicon.ico` 404 gone; `レシート` tab renamed `写真`; 「日付は推測です」 hidden when the date is today.

## Verification Today (2026-11-26)
- Fast UI sweep (`tests/ui_sweep.py`, ~15s): 10/10 steps, 0 console errors, 0 failed requests; frames p50 16.7ms, p95 ≤24ms, max 34.7ms (commitments page), dark chat p95 16.9ms — `documents/_extract/ui-sweep/report-fast.json`
- Latency bench (`tools/bench_turn.py`, 10 real Japanese turns): p50 1.0–3.0s model time, worst 17.5s with `GEMINI_THINKING=off` + 10s timeout, down from 69.6–123.6s tails before
- Suites after the rework: `test_ask` 38/38, `test_gate` 15/15, `test_confirm` 15/15, `test_commitments` 16 OK, `test_extract` 6/6
- Contrast: `#4F7075` with white 5.37:1 (AA), dark text tint `#7FA6AC` 6.76:1 on `#0f172a`
- Item photo + card trim + shell + swipe (2026-11-26, instance on 8010): suites `test_ask` 38/38, `test_gate` 15/15, `test_confirm` 15/15, `test_commitments` 16 OK, `test_extract` 6/6, `test_receipts_ask` 13/13, `test_card_trim` 12/12; journeys `shell_nav` 24/24, `chat` 12/12, `proposal_card` 12/12, `receipts` 5/5, `receipts_item` 8/8, `swipe_gestures` 13/13 at 390x844 and 1280x800; `ui_sweep` 10/10 steps, 0 console errors, frames p50 16.7ms — `documents/_extract/verify/`

## Next Steps
- 2026-11-26: **Third phone finding answered** — a photo may be the thing he bought (clothes, water, snack), not a receipt. A non-receipt photo no longer dead-ends: it lands on `/receipts`, asks 「いくらでしたか？」 with an empty required amount box, and records what he types (photo kept, `source_kind=photo`). Machine-read prices are suppressed for non-payment images, so a menu or price list cannot become an expense.
- 2026-11-26: **Fixed a real phone bug** — replies that contained a `<link>` before the card (proposals) were silently dropped by the AJAX appender, so 「先週の金曜 ランチ 1200円」 showed only his bubble. The loop iterated a live `template.content.children`; the card is now appended.
- 2026-11-26: **Proposal card trimmed** — one line with amount + category + source + short date (`11/20`), long date only when not today, warning shortened to 「日付は推測です」, hint once, both buttons kept, 直す as a muted underlined link. Detail: `docs/design/item-photo-and-card-trim-2026-11-26.md`.
- 2026-11-26: **Shell rebuilt as drawer + rail** — the owner said the UI looked awful and the pro apps "all make sidebar style". Research says none of them ship a persistent sidebar on a phone: ChatGPT and Claude use a bottom bar + history drawer, Gemini a slide-in drawer, and the ~260px sidebar is their *desktop* shape (Material 3: bar under 600dp for 3-5 destinations, rail 600-839, drawer 840+). Our thin top tab strip matched none of them. Now: off-canvas drawer below 840px (max 288px, scrim, Escape returns focus, `inert` when closed) and a persistent 248px sidebar at 840px+ with the composer offset to clear it. The chat empty state became a centred hero instead of a grey chat bubble. Palette unchanged on his instruction. Detail + sources: `docs/design/shell-navigation-2026-11-26.md`; house rules installed as the `snap-track-shell` skill.
- 2026-11-26: **AI latency measured** — direct service calls: p50 **4.98s**, p95 **14.4s** (n=9, gemini-3.1-flash-lite, thinking off, including 3 timeout retries and one 503). One UI send measured 1.1s. With the thinking budget left on, one call took **54.6s**. Frames stay at 16.7ms, so the wait is the model, not the UI. Evidence: `documents/_extract/research/latency-measured.md`.
- 2026-11-26: **Swipe card measured and improved** — 140px drag = 5° tilt, 96px commit threshold, no velocity, spring-back 60→9→0 in ~400ms (already animated). Added: hint that names both directions, horizontal-intent lock so a diagonal drag scrolls instead of saving, arrow keys now move focus to the button instead of saving instantly. Measured, not assumed: `.verify/journeys/swipe_gestures.py` 13/13. Research + decisions: `docs/design/swipe-card-research-2026-11-26.md`.
- 2026-11-26: **16 visual detail fixes** from a screenshot audit (desktop media query was dead, date field clipped 11/27/2026, contrast failures on undone/strike/pending/disabled, 40px chips, unreachable camera input, mid-word Japanese wrapping, focus rings).
- 2026-11-27: **Amount keypad shipped (owner chose Option B)** — the receipts ask screen now shows a big 44px amount field plus a drawn pad (1-9, 00, 0, けす) and 保存する in a fixed bar. It is progressive enhancement: the pad ships `hidden`, `pad.js` reveals it, sets `inputmode=none` so the phone keyboard stays down, and the real number input remains the submitted value. 分類 chips moved into the pad bar because they are required and were being clipped. 日付 is no longer force-opened and now reads 写真からは読めません when unknown. `receipts_item` journey is 16/16 (types, deletes, 00, saves ¥5,800). Options A-D mockups: `documents/_extract/report/design-proposals-2026-11-26.html`.
- 2026-11-27: **Confirm card floats (owner picked Option 2)** — the pending proposal is promoted client-side into a centred card (`.modal-wrap` + `.veil`), × / Escape / outside-tap all cancel, the card returns to the thread and can be tapped again, drag shows 保存 / やめる stamps instead of hint text, 直す is deleted, and the saved card carries 記録しました / 取り消す inside itself. Measured during the build: flex alignment left the card at y=18 (`margin:auto` fixed it to y=335) and it rendered 379px wide without `box-sizing:border-box`. Evidence: `proposal_card` 21/21, `swipe_gestures` 13/13.
- 2026-11-27: **Shade replaced blur, and the dialog focus ring removed** — the owner said the blur hid the chat he wants to read, so the veil is now a 30% tint with no `backdrop-filter`. Focusing the dialog also drew the global accent focus ring as a fat teal border around the card; `outline:none` for the modal card only. Pushed as `0cdb248`.

## Next Steps
- **Build chat corrections** (owner asked twice): edit in place, target the most recent transaction, confirm through the existing floating card. Exact steps in `docs/handoff/2026-11-27-rework-corrections-next.md`. Do not ship without a journey proving one row, amount 1250, after 「1200じゃなくて1250」.
- **Fix the four card-state blockers found in review** (not touched yet): double-answer race in `app/chat/routes.py:122-143`; answering an older card duplicates a newer one; cancel overwriting an already-saved card; a today-inferred chat save skipping the promised confirmation. Full detail: `documents/_extract/research/bug-hunt.md` (gitignored — copy into a tracked doc if needed on another machine).
- Design review still open: the desktop sidebar has a dead zone between the three items and the account row (a "this month" total would fill it honestly); the header `h1` duplicates the active nav label on desktop; suggestion chips are still outline pills.
- Untested: iOS Safari at all, real touchscreen swipe (all swipes are synthetic mouse drags), keyboard-only use end to end, AI-timeout/quota error states.
- Live tests must call the browser window to the foreground; otherwise the owner sees nothing and the run looks fake.
- `docs/test-walkthrough.md`, `docs/handoff/2026-11-27-rework-corrections-next.md` and the design docs are tracked; the rework lives on branch `feat/phone-rework` (pushed, commits `93861f8` and `0cdb248`). `main` is still clean at `a235733`.
- A stray instance still listens on 8011 (old code); needs an owner decision, not a silent kill.
