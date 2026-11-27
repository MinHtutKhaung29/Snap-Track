# Test the app on your phone — 2026-11-26

Everything below was run just now against the live server, so the "should see" text is copied from the real screens, not guessed.

## Before you start

No Wi-Fi sharing needed. A free Cloudflare tunnel carries the app out to a public address, so any phone with mobile data can open it:

**https://contribute-kinase-afford-riding.trycloudflare.com**

Three things about that link:

- It is temporary. It dies when the tunnel or this computer stops, and a restart gives a different random name. Ask me and I hand you the current one.
- It is public. Anyone holding the link can open the sign-up page, so use a throwaway password and do not upload real bank screenshots — the sample picture in `documents\_extract\fixtures\payment_screenshot.png` is enough.
- Fallback if the tunnel is down: phone hotspot, computer joins it, then the address becomes `http://192.168.43.x:8010`. Port 8010 is already open to the local subnet (rule `Snap and Track 8010`).

## What to test, and what a correct screen looks like

### 1. Sign up

Tap 新規登録, type any name, email and the same password twice, tap the blue button.

**Should see:** a chat page with the tabs チャット / レシート / 支払い予定, a card that says 「こんにちは、〈your name〉 さん」 and 「支出や質問をそのまま送ってください。」 plus two example buttons 「今日 ランチ 850円」 and 「今月の食費いくら？」.

### 2. Type a payment

Type `今日 ランチ 850円` and tap 送信.

**Should see:** your message in a blue bubble on the right with a time, then a light card below it reading **−¥850**, then on one line **食費** with a blue dot, **ランチ**, **2026年11月26日（木）**, and the time again. Under the card: 「記録しました　取り消す」.

### 3. Undo it

Tap 取り消す.

**Should see:** the same card turn into **¥850** (no minus), the words **取り消し済み** in the middle, and 取り消す disappears.

### 4. Photograph a payment

Tap the camera/picture icon inside the message box. On the phone choose **カメラ** and point at a receipt, or **ファイル** and pick the sample picture on this computer:
`documents\_extract\fixtures\payment_screenshot.png`

**Should see:** the レシート tab opens with the photo at the top (tap 拡大 to enlarge), 「確認待ち　1/1」, then three rows:

| row | should read |
|---|---|
| 金額 | ¥3,200 |
| 日付 | 2026年11月25日（水） |
| 店・内容 | 東京電力エナジーパートナー |

and six category chips with **光熱費** already chosen, a big blue **保存する**, and a quiet 「この画像を捨てる」 at the bottom. A long shop name wraps onto more lines instead of ending in `…`.

### 5. Save it

Tap 保存する.

**Should see:** the card is gone and the page says 「未確認の写真はありません」「チャットの写真ボタンから追加できます。」with a blue チャットへ.

**Will not see:** any message in the chat telling you the ¥3,200 was saved. That is a real gap — the record exists, but the chat stays silent. Tell me if you want that fixed next.

### 6. A bill that comes back every month

In the chat type `家賃 85000円 27日払い`.

**Should see:** a card 「この支払い予定を作りますか？」 with **¥85,000**, 家賃, a category, 「毎月27日」, 「初回 2026年11月27日（金）」, the note 「作成しても支出にはなりません。支払ったときに記録されます。」, and the buttons **作成する** / **やめる**.

Tap 作成する, then open the 支払い予定 tab.

**Should see:** a card with 家賃 **¥85,000** and 「毎月の支払い」, rows 次回 2026年11月27日（金）, 分類, 支払済み 0 回, a greyed-out 支払った and the hint 「支払期日が来ると押せます。」

**One thing that is wrong here:** 家賃 lands in **光熱費**, because the plan only has six categories (食費・交通費・日用品・交際費・光熱費・その他) and rent has no home of its own. Say the word if you want a 住居費 category.

### 7. Dark mode

Switch your phone to dark mode (or turn the screen brightness theme in the phone settings), then reload the page.

**Should see:** the same three screens with a near-black background and light text, no white flashes, and the blue buttons still readable.

## What does not exist yet

- The monthly summary (「今月いくら使った？」 gets an answer in chat, but there is no summary page).
- Any confirmation in the chat after saving a receipt photo (step 5).
- 支払った stays greyed out until the due date; you cannot mark a bill paid early.
- Comments in code, lints, and dynamic collision detection are deliberately out of scope for this project.

## If something looks wrong

Tell me the step number and what you saw instead — a phone screenshot is even better. Every screen above also exists as a picture in `documents/_extract/theme/flow-*.png` if you want to compare side by side.
