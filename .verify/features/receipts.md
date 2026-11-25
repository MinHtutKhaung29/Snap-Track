# Receipts

Photograph a receipt, have the model read it, confirm with one gesture, and let the row carry the photo.

## Sub-features

- Upload a photo from the chat screen (📷) — the only entry point today
- Queue of pending reads with a `1 / N` counter
- Swipe right to save, swipe left to open the fix form; the same three actions exist as buttons
- Fix state: 金額 / 日付（要確認） / 店・内容 / 分類, with typed values preserved across a validation error
- Discard a read permanently (`✕ 捨てる`, plus `このレシートを捨てる` inside the fix form)
- Failed reads (unreadable, or daily AI cap reached) are shown as cards that can be fixed or discarded

## How to get to it (user POV)

From `/chat`, tap 📷. The file picker opens with the camera. After the read, the app lands on `/receipts`. The header links back to チャット.

## Driving it with Playwright

```python
page.goto(BASE + "/chat")
page.set_input_files('input[name="photo"]', "documents/_extract/p005/real/r02.jpg")
page.wait_for_url("**/receipts", timeout=180000)
```

- Card: `.swipe` (contains `.shot` image, `.amt`, `.meta` pills)
- Actions bar: `.actions` with `button.danger`, `#fix-btn`, `.primary`
- Fix form: `details#fix` → `.form.tight input[name="amount"]`, `input[name="date"]`, `input[name="shop"]`, `select[name="category_code"]`
- Error banner: `.err` with `role="alert"`

## Gotchas

- The photo input exists **only on `/chat`**. After a save the app is on `/receipts`; navigate back before uploading again or the selector waits forever. This has burned a run already.
- A receipt with no readable date opens the fix state with the date pre-filled to today and labelled 日付（要確認）. Saving with the field cleared must show 「日付を入れてください」 and write nothing — never substitute a date on the server.
- While the fix state is open the action bar is deliberately hidden, so exactly one primary button exists. A run that asserts two save buttons is asserting a bug.
- Uploads larger than 5 MB are rejected from `Content-Length` before the body is read (413). A 7 MB POST is the check.
- The receipt OCR consumes the same `ai_usage` budget as chat; over the cap nothing is written and no receipt row is created.
- Standing rule: a photo card is always confirmed by the user. Chat can auto-save when the user's own digits and an explicit date are present; a photo never can.
