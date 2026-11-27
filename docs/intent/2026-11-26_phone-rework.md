# Intent — phone review rework (send button, swipe ask-back)

Date: 2026-11-26
Owner: repo owner (phone acceptance pass of M4)
Status: approved in part — send arrow only (owner, 2026-11-26); ask-card deferred to a later approval.

## Scope changes (R-CHANGE)

- 2026-11-26 — Owner: "Approve only the send arrow first — show me that before touching the ask flow." C2 and its builder wave are deferred; C1 was delivered solo in the parent checkout (2 files, small diff). C4 reduced to the composer check until the card exists.

## Problem

1. The composer send control is a 44px accent circle holding the word `送信`. The owner asked for the pattern the big chat apps use: an icon-only arrow.
2. When the assistant needs an answer ("lunch 700" with no amount/date detail), it replies with plain text. The owner wants that ask-back to be a Tinder-style swipe card (yes / no) while typing in the composer still works.
3. The owner has never seen the UI exercised by a machine: no click-through, no screenshots, no recording. She asked why, and wants PC + mobile verification after the fix.

## Answers (R-ASK log)

- Q: arrow or paper plane? A: arrow (owner named Messenger / ChatGPT / Telegram as the reference family). — 2026-11-26
- Q: what happens to typed answers when a card is shown? A: typing always stays available; the card is an accelerator, not a gate. — owner statement 2026-11-26

## Success criteria

- C1 — Composer send control is an icon-only arrow inside a 44x44 target, with `aria-label`/`title` = 送信, no visible text, and a disabled state when the field is empty (composer spec §5).
- C2 — When the assistant must ask before recording, it emits a structured ask-back and the chat renders a swipeable yes/no card: swipe right = yes, swipe left = no, both also reachable by tap and keyboard, typing in the composer unaffected.
- C3 — No regression: existing pytest suite passes unchanged, no test deleted or skipped.
- C4 — Visual evidence exists at 390x844 and 1280x800, light and dark, for chat (with card), receipts and commitments; produced by an automated click-through run, not hand-waving.
- C5 — Research note with source URLs records what the reference apps do (send glyph, swipe-to-answer affordances) and what we copied or rejected.
- C6 — `MEMORY.md` and `DECISIONS.md` updated; nothing pushed.

## Non-goals

- No monthly-summary work, no new categories, no schema migration.
- No redesign of receipts/commitments beyond what the card CSS touches.
- No public tunnel, no push, no merge to `main` without owner word.

## Plan

1. P1 research + recon (read-only lanes) — evidence for C5, code map for C2.
2. P2 intent approval (this doc).
3. P3 builder wave in isolated worktrees: send icon lane, ask-card lane, UI-check tool lane.
4. P4 parent integration: merge, pytest, run UI check, capture evidence.
5. P5 owner review on phone + PC, then notebook update.

## Criteria verdicts

- C1 — PASS. Icon-only up-arrow in a 44x44 circle outside the pill, `aria-label`/`title` = 送信, inert grey state when empty. Evidence: `documents/_extract/ui-send/*.png` (four viewports), `BOX … 44x44`, `SUBMIT ok … bubble=1`, `tests/ui_send.py`.
- C2 — deferred by owner 2026-11-26; not attempted.
- C3 — PASS for the unit scripts: gate 15/15, confirm 15/15, commitments OK, extract 6/6. `smoke_chat.py` timed out on its own live AI call — recorded as a risk, not claimed green.
- C4 — partial: composer captured at 390x844 and 1280x800, light and dark, with a real click-through; receipts and commitments not re-captured (unchanged surfaces).
- C5 — PASS in substance: `docs/design/ui-review-2026-11-26.md` carries the glyph table with sources and the arrow-vs-paper-plane split.
- C6 — not done yet; notebook update runs when the ask-card phase closes.
