# Chat (home surface)

One permanent thread per user. Every money action is either saved immediately or held as a proposal card.

## Sub-features

- Type a sentence and have an expense or income filed
- The confirmation gate: inferred date or inferred amount produces a card, not a row
- Edit a proposal in place (金額 / 日付 / 分類) before saving
- Cancel a proposal
- Undo a saved entry within 24h (`取り消す`)
- Ask a question; the total is computed in SQL
- Camera button hands off to the receipts surface

## How to get to it (user POV)

`/` redirects to `/chat` when signed in, or to `/login` when not. The header has レシート and ログアウト. The composer is fixed at the bottom with a 📷 button above it.

## Driving it with Playwright

```python
page.fill('[name="message"]', "今日 ランチ 850円")
page.press('[name="message"]', "Enter")
page.wait_for_function("() => document.getElementById('chat-form').dataset.busy === '0' "
                       "&& !document.querySelector('#thread .thinking')", timeout=180000)
```

- User bubble: `#thread .msg.me` (appears instantly, before the reply, because the page uses fetch)
- Saved card: `#thread .msg.bot.entry` with 記録しました
- Proposal: `#thread .msg.bot.entry.pending` with `保存する` and `やめる`
- Thinking indicator: `#thread .thinking` (present while waiting)
- Answer: `#thread .msg.bot.answer` containing 合計

## Gotchas

- Waiting on `networkidle` proves nothing here: the form never navigates. Wait on `data-busy="0"` and the absence of `.thinking`, otherwise the assertion runs before the reply exists.
- The gate is the feature. A message with an inferred date must write **zero** rows until 保存する. Verify by counting `transactions` rows before and after, not by reading the screen.
- 「先週」「来月」 are inferred dates and must produce a card; 「今日」「昨日」 and `2026-11-20` are explicit and save immediately.
- Numbers that are not money must not pass the gate: `2025-11-20` (a date), `10%`, `3個`. `tests/test_gate.py` holds those cases.
- Undo is limited to 24h by database clock; an older row must stay in place and produce 「24時間を過ぎた記録は取り消せません。」.
- A double submit must not write twice; `tests/test_confirm.py` proves the row lock.
