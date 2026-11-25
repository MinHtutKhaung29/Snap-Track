# Handoff — Snap & Track: UI foundation complete (2026-11-25)

## Mission anchor (verbatim; do not paraphrase)
- Goal: A Japanese graduation project — a spending tracker where the user types or photographs a payment in chat and gets a confirmed record.
- Master plan: docs/base-plan.md
- Docs / links: docs/design/chat-ui-spec.md · documents/_extract/reviews/p3-plan.md · MEMORY.md · DECISIONS.md
- Current milestone: M4 — definition of done: every surface (chat, receipts, commitments) passes its suite, renders correctly in light and dark at 390x844, and a photographed payment screenshot becomes a persisted record carrying amount, date and recipient.
- Non-goals / hard constraints: whole yen only, never float; chat is the interface, not a dashboard; free tiers only (Gemini + local MySQL); no comments in code; templates are generated and never hand-edited; only the owner restarts the server.

## Operating state
- Branch `feat/p1-auth` @ `34a7b21`. All work sits here, **not on `main`** — reconciliation is item 1 of the queue.
- Server `127.0.0.1:8010`, no reload. Restart required after any Python change.
- Tunnel `https://agree-ministry-hitachi-breakfast.trycloudflare.com`.
- Pools: Antigravity Claude/GPT was at 0% (resets ~10:23Z); OG (deepseek/mimo) and Gemini healthy. Do not dispatch Claude lanes into an empty window.
- Owner decisions this session: light theme default with dark on system preference; a bill never auto-posts; the AI may not create categories; payment screenshots are first-class evidence, not only paper receipts.

## Teaching state (owner-facing)
- Concepts introduced: optimistic UI → bubble renders before the server answers; CSRF token rotation → why signing in must not wipe the token; writer isolation → one lane per physical checkout; due-date clamping → `min(due_day, last_day_of_month)` instead of adding days; installment remainder → the final payment absorbs the division remainder.
- L1 status of the phase: **verified** — all seven suites, both colour schemes, the recipient round-trip. **Assumed** — iOS keyboard behaviour under `interactive-widget` (has a `visualViewport` fallback, unverified on device). **Pending** — owner's eye on the dark surface being darker than the page.

## Verified completions
1. Chat, receipts and commitments pass together — evidence: `test_gate 15/15`, `test_confirm 15/15`, `smoke_auth 10/10`, `test_commitments OK(16)`, `test_extract 6/6`, `ui_instant 8/8`, `ui_image_forms 11/11`, `.verify chat journey 9/9` on `34a7b21`.
2. A photographed payment screenshot becomes a record with its recipient — evidence: `{'amount': 3200, 'source': '東京電力エナジーパートナー', 'category_id': 5, 'source_kind': 'photo'}` from `ui_image_forms`.
3. Due dates clamp and return without drift — evidence: `2027-01-31 → 2027-02-28 → 2027-03-31` printed by `test_commitments`.
4. Installments sum exactly — evidence: `[16666 x5, 16670] = 100000` printed by `test_commitments`.
5. Light and dark both legible — evidence: `documents/_extract/theme/contrast.py` → ALL CHECKS PASS, body 17.85:1 light / 15.15:1 dark.
6. Design tokens are sourced, not invented — evidence: `docs/design/chat-ui-spec.md`, read from `Ajaxy/telegram-tt` via `gh api`.

## Decision log (rejected options + rationale)
- Sign-out placement: kept visible in the header because hiding it behind a menu on a phone is a regression; rejected the ⋯ menu and corrected the spec instead.
- Input growth: chose `<textarea rows=1>` because a 5-line cap is impossible for `<input type=text>`; rejected keeping the input and dropping growth.
- Selector widening: allowed `input[name="message"] → [name="message"]` across four harness files, fenced to that single token; rejected editing assertions.
- Server echo: client now inserts only non-`.me` nodes; rejected removing the optimistic bubble because it would reintroduce latency.
- Dark surface: kept darker than the page per source evidence; rejected inverting it without the owner's look.

## Known unknowns / risks
- iOS keyboard inset is unverified on a real device; the `visualViewport` fallback has not been exercised on hardware.
- Branch divergence: `feat/p1-auth` carries four unreleased commits.
- The chat greeting card persists after messages exist — cosmetic but visibly wrong.
- Bubbles carry no timestamps, contrary to spec §4.
- Two builders hit the 30-minute lane timeout while still working; UI tasks must be split smaller.
- A partial test run caused a three-commit regression (`毎月の支払い`). Always run all seven.

## Next-phase queue
- Continue: reconcile `feat/p1-auth` into `main`, tag, push — owner gate: yes (decides what gets submitted).
- Continue: fix greeting-card condition and add bubble timestamps — owner gate: no, evidence: captures plus `ui_instant`.
- Continue: monthly summary surface for the demo — owner gate: yes (new scope).
- Continue: owner review of the dark surface call — owner gate: yes, evidence: `documents/_extract/theme/*-dark.png`.

## Safety constraints
- Never edit `AGENTS.md`.
- Never hand-edit generated templates; edit the generator and regenerate.
- Never restart the server on the owner's behalf without asking.
- Never edit tests to make a builder's work pass; a selector widening must be declared and diffed.
- Preserve `documents/_extract/` as evidence; route temporary captures to `%TEMP%`.
- Exactly one writer per checkout; writers go in worktrees, max three per wave, integrated one at a time.
