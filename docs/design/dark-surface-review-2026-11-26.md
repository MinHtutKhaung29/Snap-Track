# Dark-surface review — 2026-11-26

## Open the pictures here

http://127.0.0.1:18081/

Six files, each 390x844, light and dark of the same screen:

- `chat-light.png` / `chat-dark.png`
- `receipts-light.png` / `receipts-dark.png`
- `commitments-light.png` / `commitments-dark.png`

Old versions from yesterday 15:59 are kept in `documents/_extract/theme/prior-20261125T1559/` so nothing was lost.

## Why the pictures you were told to review were wrong

The handoff pointed at captures taken at 15:59 on 2026-11-25. Three changes landed after that, so those pictures no longer matched `main`:

| commit | time | what changed |
|---|---|---|
| `84bc7d1` | 18:11 | the receipt card keeps the recipient the extractor reads |
| `c5ef2a6` | 18:12 | composer became a textarea, camera moved inside the pill |
| `d2e9d51` | 19:24 | greeting leaves on first message, appended replies get a clock |

Proof the old receipt picture was wrong: it showed 店・内容 = 未入力 while the same screenshot plainly reads 東京電力エナジーパートナー, and the database shows that value was captured (receipt #95 → transaction 350, `source_kind=photo`). The fresh capture shows the recipient on the card in both schemes.

The capture script itself was also broken against current markup: it filled `input[name="message"]`, but the composer has been a `<textarea>` since `c5ef2a6`, so the re-run hung until its 4-minute timeout. One-line selector fix in `documents/_extract/theme/capture.py` (evidence tooling, gitignored — no app code touched). Re-run finishes in 18 s and reports every palette assertion holding.

## What I checked before trusting the handoff

- `main` = `origin/main` = `c2f6793`, tag `m4-ui-foundation` present, working tree clean apart from the untracked handoff doc — matches.
- `documents/_extract/theme/contrast.py` re-run just now: **ALL CHECKS PASS** (token pairs, relationship rules, hardcoded-hex sweep) — matches.
- Capture freshness — **did not match**, fixed above.
- Handoff deferred item 2 ("`_commitment_msg.html` never renders `show_time`") — **does not match the code**. `_commitment_msg.html:45` renders `show_time`, and `app/chat/routes.py:82` passes it, same as the chat partial. If commitment cards still show no clock, the cause is elsewhere; do not spend a session editing that template until it is re-checked.

## What the fresh pictures show

Chat, both schemes: one pill, gallery/camera glyph left, round 送信 right, clock on both bubbles (10:35), card amount `−¥850` dominant, 食費 / ランチ / 2026年11月26日（木） on one line, 記録しました・取り消す quiet underneath. Dark reads well; the accent circle is bright but passes the sweep.

Receipts, both schemes: thumbnail with 拡大 ∨, 確認待ち 1/1, three full-bleed rows (金額 ¥3,200 · 日付 2026/11/25 · 店・内容 東京電力エナジーパートナー), six category chips with 光熱費 selected, full-width 保存する, quiet この画像を捨てる at the bottom.

Commitments, both schemes: overdue 家賃 card outlined amber with 期限超過 in red, 電気代 due today, 洗濯機 installment with 0 / 6 回 and 残り 6 回 and a disabled 支払った plus 支払期日が来ると押せます。

## Candidate adjustments, for you to accept or drop

1. **Date style differs between surfaces** — chat says `2026年11月26日（木）`, receipts say `2026/11/25`. Same fact, two spellings. Cheap: one formatter at the render site.
2. **Recipient text has no room to grow** — 東京電力エナジーパートナー already reaches the right edge at 390 px. A longer transfer name (e.g. a card statement payee) has nowhere to go; needs wrap or ellipsis, and a test with a long name. Not yet reproduced, so it is a risk, not a proven defect.
3. **Two card grammars** — chat cards are rounded and inset, receipts and commitments are full-bleed rows with dividers. Consistent within each surface, different between them. Pure taste until you say otherwise.

## Evidence

- Fresh captures: `documents/_extract/theme/*.png` (2026-11-26 10:35)
- Previous: `documents/_extract/theme/prior-20261125T1559/`
- Contrast: `.venv/Scripts/python.exe documents/_extract/theme/contrast.py` → ALL CHECKS PASS
- Readiness: `.venv/Scripts/python.exe C:/Users/minht/.pi/agent/skills/verify-web-app/verify.py doctor --project .` → DRIVABLE, `model=gemini-3.1-flash-lite`, `tables=8`

## Decision — 2026-11-26, approved

Owner chose: unify the date style **and** check/fix long recipient names at 390 px.

## What changed

- Date: `app/receipts/routes.py` feeds `card.date_label` (the existing `jp_date` helper, also used when a validation round-trip supplies an override date), and the template prints it. `2026/11/25` became `2026年11月25日（水）`, the same spelling as the chat card.
- Payee: the shop row is now `row-shop`, and `.row-shop .row-v{white-space:normal;overflow-wrap:anywhere}` lets it wrap. `base.css` still ellipsises every other row value, which is right for amounts and dates.
- Measured at 390x844, not eyeballed: before, a long payee put 658 px of text into a 290 px box (`text-overflow:ellipsis`, unreadable past モ…); after, `scroll == client`, three lines, no horizontal page overflow. `shop-long-before.png` / `shop-long-after.png`.
- The `.verify` receipts journey asserted `.swipe`, a class the M4 rebuild deleted, so it could not pass and was never in M4's evidence. It now checks the card, the Japanese date form, and the long-payee wrap: **5/5** both on a working-tree instance (8021) and on the live server (8010).
- Captures regenerated from the working tree; `contrast.py` re-run after the CSS change: ALL CHECKS PASS.

## Two things found along the way, not fixed

1. **A stray server is listening on 8011** (pid 20668, old code, not started by this session). Verification pointed at 8011 would silently test stale code. Closing it is an owner decision.
2. **The handoff's deferred item 2 is wrong.** `_commitment_msg.html:45` renders `show_time` and `app/chat/routes.py:82` passes it, exactly like the chat partial. Whatever produced that observation, it is not a missing template line — re-check before assigning a session to it.

## Where the new evidence lives

- Captures: `documents/_extract/theme/*.png` (2026-11-26, post-fix); older sets in `prior-20261125T1559/` and `prior-20261126T1035/`
- Payee wrap: `shop-long-before.png`, `shop-long-after.png`
- Journeys: `documents/_extract/verify/20261126T014956Z-receipts` (8010), `20261126T014931Z-receipts-standalone` (8021)
- Suites: `ui_image_forms` 11/11, `test_extract` 6/6, `contrast.py` ALL CHECKS PASS

## Still needs you

1. Restart 8010 when convenient — the date/override line is Python; templates and CSS are already live.
2. Say whether the stray 8011 instance may be closed.
3. Pushed for review as PR #4 (`fix/date-style-and-long-recipient`, 6 files + the handoff note). Merging is the owner's call; nothing was merged.
