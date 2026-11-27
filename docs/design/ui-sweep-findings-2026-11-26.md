# Live UI sweep — what was tested, found, and needs fixing (2026-11-26)

Run against the real app in a visible 390x760 Chromium window on `127.0.0.1:8010`, driving with `playwright-cli` and `tests/ui_sweep.py`.

## Tested, with evidence

| area | result | evidence |
|---|---|---|
| Frame smoothness, chat | 60fps, p95 gap 17ms, max 17–33ms | `documents/_extract/ui-sweep/quick-frames.json` |
| Frame smoothness, receipts | 60fps, p95 17ms, max 17ms | `quick-frames2.json` |
| AI turn latency after the fix | 1.09s server round-trip, twice | `live-speed.json`, `live-speed-2.json` |
| Login / logout / re-login | pass | `ui_sweep.py` steps, screenshots |
| Send a record | pass, card renders | `live-speed-01.png` |
| Ask card, tap yes | pass, card collapses to answered | `ask-03-swiped.png` |
| Proposal save via swipe | pass, card becomes 記録しました | `swipe-04-after.png` |
| Undo 取り消す | pass (sweep step) | `ui-sweep/dark-06-undone.png` |
| Tab navigation チャット↔レシート↔支払い予定 | pass, no failed requests | `quick-02/03/04` screenshots |
| Details 直す disclosure | pass | `ui-sweep/*-07-details.png` |

## Found (ordered by user impact)

1. **「レシート」 means photographed receipts only** — FIXED: tab renamed `写真`; the page's empty state already said 「未確認の写真はありません」 and linked to chat, so only the label was misleading.
2. **`/favicon.ico` 404s on every page** — FIXED: inline SVG data-URI icon in `base.html`.
3. **Composer focus ring paints the whole pill in accent blue** — FIXED: border stays neutral, a 3px `--pick-bg` halo marks focus (`ui-sweep/fast-05-focus.png`).
4. **The oldest visible bubble can slide under the sticky header** — NOT REPRODUCED in the click sweep; it needs mid-thread scrolling, which is normal sticky behaviour. Left alone rather than adding padding to every screen.
5. **「日付は推測です」 shows for today's date** — FIXED in `settle_record`: suppressed when the inferred date is today, still shown when it differs (`test_confirm` 15/15 after the change).

### Also fixed in the same pass

- `レシート` tab renamed `写真` (the page only lists photographed receipts; its empty state already pointed to chat).
- `/favicon.ico` 404 removed with an inline SVG data-URI icon — 0 favicon requests, 0 console errors in the fast sweep.

## Not tested yet (honest gaps)

- Photo / camera upload path (file chooser not exercised), including the OCR result screen.
- Commitments actions (only one button existed on that page at the time).
- Full dark-mode click pass (dark screenshots exist, but the run aborted early).
- Keyboard-only operation and swipe on a real touchscreen.
- Error states: AI timeout, quota reached, invalid amount.

## Fix order suggested

1. Receipts empty-state/rename (prevents "my data is gone" panic).
2. Favicon 404 (cheap, removes console noise).
3. Focus ring and header overlap (visual polish).
4. Date-guess note suppression for same-day records.
