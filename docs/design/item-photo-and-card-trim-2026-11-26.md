# Third phone finding + proposal-card trim (2026-11-26)

## What the owner said

> "the third is if i send the photo it may not a receipt or text include but it may be the things i bought. like clothes or water bottle or snack or juice, i just send images of product i buy and send price i used, or if not you asked to me like that"

And when asked how the two should meet:

> "Photo first — I pick the photo, it lands, the app asks 「いくらでしたか？」, I type the price"

So: the photo may be the **thing he bought**, not a receipt. The app must never read a price off it. It asks, he types, it records.

## Three defects found while answering it

1. **A non-receipt photo dead-ended.** `_render_queue` sent any image with no amount and `is_payment: false` to a refusal screen: 「お支払いとして読み取れませんでした」 plus two links. The ask-for-a-price form already existed ten lines below; the branch order prevented it from ever being reached.
2. **The proposal card never appeared after an in-page send.** Sending 「先週の金曜 ランチ 1200円」 stored a correct pending proposal (message 750, date 2026-11-20) but the browser showed only the user bubble. Cause: `chat.html` appended nodes while iterating the *live* `template.content.children` collection. Each `appendChild` removes the node from the fragment, shifting the collection, so the element after the stylesheet `<link>` was skipped. Two-node replies (saved) survived; three-node replies (proposal = user echo + link + card) lost the card. On his phone that reads as "nothing happened".
3. **The proposal card was seven stacked rows** — label, 34px amount, category+source, long date, two-line warning, hint, buttons, 直す, time.

## What changed

| File | Change | Why |
|---|---|---|
| `app/receipts/routes.py` | `_card_state()` pulled out and used by `_render_queue`; the `unreadable` branch deleted; machine-read amount suppressed when `is_payment` is false; `save` ignores a stored amount for non-payment images | an item photo now reaches 「いくらでしたか？」 instead of a refusal; a price list's printed number can never become an expense |
| `app/receipts/extract.py` | prompt and system line accept "a photo of something the user bought with no price in the picture" → `amount: null`, `is_payment: false`, `evidence_type: other`, `source` = brand/shop | the model must not invent a price from an item photo, but should still name the shop |
| `tools/make_receipt_assets.py` | the dead `unreadable` block deleted, heading → 「いくらでしたか？」, shot label always 確認待ち; regenerated `receipts.html` + `receipts.css` | the generator is the source of truth for those two files — verified byte-identical (4949/4420) before editing |
| `app/chat/templates/chat.html` | `Array.from(t.content.children)` | stops the skipped-node bug |
| `app/chat/templates/_msg.html` | proposal card: one `.line` with amount + category + source + short date, long date only when not today, warning shortened to 「日付は推測です」 | three rows become one; buttons kept, 直す kept |
| `app/chat/service.py` | preview gains `date_short` (`11/20`) and `is_today` (compared against `today_jst`) | the card needs a short date and a today test |
| `app/static/chat.css` | `.line` rules, `.edit > summary` becomes a muted underlined link | implement the trim, keep the 44px tap target |
| `tests/test_receipts_ask.py` | 13 checks | the four decisive card states, no HTTP needed |
| `tests/test_card_trim.py` | 12 checks | template-level proof of one line, hidden date, one warning |
| `.verify/journeys/receipts_item.py` | new journey | a non-receipt image → ask → typed price → saved row |
| `.verify/journeys/proposal_card.py` | new journey | geometry, wording, save, and the "asks back when the amount is missing" path |

## Evidence

Suites (working tree, 2026-11-26): `test_ask` 38/38 · `test_gate` 15/15 · `test_confirm` 15/15 · `test_commitments` 16 OK · `test_extract` 6/6 · `test_receipts_ask` 13/13 · `test_card_trim` 12/12.

Journeys at 390x844 against a working-tree instance on 8012:
- `receipts_item` 8/8 — txn 611, amount 5800, source スニーカー, `source_kind=photo`, receipt 112
- `receipts` 5/5 — a real receipt still auto-reads (620) and saves
- `proposal_card` 12/12 — one row, short date, 直す link, saves; 「今日 ランチ」 asks back and writes nothing
- `chat` 12/12 — saved, confirm, undo, SQL answer all still work

`tests/ui_sweep.py` (headless, 390x740): 10/10 steps, 0 console errors, 0 failed requests, frames p50 16.7ms.

Before/after of the card: `documents/_extract/verify/20261126T163453Z-chat-standalone/shots/02-chat-proposal.png` (before, 7 rows) vs `documents/_extract/verify/20261126T164212Z-proposal_card-standalone/shots/01-past-card.png` (after, one row).
Item-photo flow: `documents/_extract/verify/20261126T162411Z-receipts_item-standalone/shots/01-item-asks-price.png`.

## Residual risks and open items

- **8010 still runs the old code** (pid 17532). Nothing reaches his phone until it is restarted.
- A freshly appended swipe card is briefly drawn in ask.js's `pending` state (buttons at 60% opacity) before it settles; the save click still lands, but the flicker is visible.
- The receipts date row says 「教えてください」 while the native date field already shows today. Pre-existing, not touched here.
- `test_extract` only exercises two fixtures; the new "item photo" prompt sentence is verified by behaviour (the journey) rather than by a third fixture.
- Still open from the handoff: dark accent `#7FA6AC` vs `#4F7075` at 3.32:1, and whether the tabs stay チャット / 写真 / 支払い予定.
