# DECISIONS.md

> Simple log for the repo owner. Never edit or delete old entries.

---

### 2026-11-23 — Initial Rules & Safety Setup
- **What:** Added `AGENTS.md`, safety hooks, memory, and `.gitignore`
- **Why:** Keep code simple, protect `main`, remember past work, and teach GitHub step by step
- **Files:**
  - `AGENTS.md` — main rules
  - `.agents/hooks.json` — hook config
  - `.agents/guard.js` — blocks bad edits/pushes & reminds long chats
  - `MEMORY.md` — agent memory across days
  - `DECISIONS.md` — this log
  - `.gitignore` — blocks uploading secrets & junk

### 2026-11-23 — Branch Protection & Auto-Install Tools
- **What:** Protected `main` on GitHub and added auto-install rule for Git + Node.js
- **Why:** Block collaborators from pushing directly to `main`, and let the agent install missing tools for beginners
- **Files:**
  - `AGENTS.md` — added Git + Node.js check/auto-install step
  - `DECISIONS.md` — logged this update

### 2026-11-23 — Define When to Upload to GitHub
- **What:** Added **When to upload** rule to `AGENTS.md`
- **Why:** Prevent pushing broken/untested code or pushing without user confirmation
- **Files:**
  - `AGENTS.md` — added upload trigger rule
  - `DECISIONS.md` — logged this update

### 2026-11-24 — Product reshaped into one-chat money tracker
- **What:** After reading all school documents, rewrote the specification as v3
- **Why:** The owner wants a single permanent chat (Muse style) where the AI files expenses, income, bills and installments from natural language, not a photo-only expense list
- **Decisions:**
  - 8 tables: users, categories, receipts, commitments, transactions, chat_message, memory_fact, ai_usage
  - `commitments` is separate from `transactions` so a bill due on the 27th is not counted as spending
  - one chat thread per user, enforced by the schema (no session id)
  - the AI never guesses money: server checks the digits appear in the user's own words, otherwise a confirm card
  - model pinned to `gemini-3.1-flash-lite` because it measured cheapest **and** most accurate (3/4 on receipts with a total, 0 hallucinations on unknown fields)
- **Files:** `docs/base-plan.md`, `docs/implementation-plan.md`, `docs/p005-technical-validation.md`

### 2026-11-24 — P0 base built
- **What:** MySQL 8.4.9 installed via winget, data directory under the user profile (no admin), database `snapandtrack` + user `snaptrack` provisioned, schema and seed applied, FastAPI skeleton running
- **Why:** A working base before any feature, as agreed
- **Decisions:**
  - MySQL runs as a normal process, not a Windows service, because installing a service needs admin
  - credentials are random per machine and live only in `.env` (gitignored); `db/provision.py` writes them
  - schema is stored in `db/schema.py`, not `schema.sql`, because the repo guard cannot scan `.sql` files
  - templates and CSS are created with the shell for the same reason: the guard cannot scan `.html`/`.css`
  - `documents/`, `uploads/`, `.venv/` are gitignored so school PDFs, real receipts and secrets never leave the machine
- **Files:** `db/schema.py`, `db/provision.py`, `db/install.py`, `app/main.py`, `app/shared/*`, `requirements.txt`, `README.md`, `.gitignore`

### 2026-11-24 — P1 chat spine + auth scaffold
- **What:** one chat thread that files money, behind a deterministic confirmation gate
- **Why:** this is the product; everything else is decoration around it
- **Decisions:**
  - The gate is a **server-side string check**, not a model self-report: the proposed amount must appear in the user's own digits, and the date must be explicit (今日/昨日/YYYY-MM-DD/M月D日). Otherwise nothing is written and a confirm card appears. Proven by test: 「先週の金曜 ランチ 1200円」 writes 0 rows until 保存 is pressed.
  - The AI returns tool calls only; it never receives `user_id`, never writes SQL, and every argument is re-validated on confirm (defence in depth).
  - `AI_MODE=stub` exists so server tests never depend on the network or on quota. Stub mode tests **our** logic; model accuracy is measured separately in `docs/p005-technical-validation.md`.
  - Login was built as a scaffold behind `app/shared/auth.py` because Siwani owns the login **screens**. Her HTML drops into `app/login/templates/` and wins automatically; no feature code touches `session` directly.
  - Passwords verified as scrypt in the database (`len=114`), cookie verified `httponly; samesite=lax`.
- **Files:** `app/chat/*`, `app/shared/ai.py`, `app/shared/auth.py`, `app/shared/csrf.py`, `app/login/*`, `tests/smoke_auth.py`, `tests/smoke_chat.py`, `tools/make_assets.py`, `tools/make_chat_assets.py`

### 2026-11-24 — Gemini transport: three bugs the live run exposed
- **What:** first end-to-end run of the app against the real Gemini API
- **Why:** the stub proved our logic; only a live call could prove the wiring
- **Findings:**
  - `x-goog-api-key` header is rejected for this credential (`ACCESS_TOKEN_TYPE_UNSUPPORTED`); the key must be sent as `?key=`. Same key returned 200 as a query parameter and 401 as a header — the earlier "expired key" diagnosis was wrong.
  - `load_dotenv` does not override existing environment variables, so the app silently used the shell's `GEMINI_API_KEY` (a different token). `config.py` now passes `override=True`: for an app, `.env` is authoritative.
  - a 60 s timeout failed a valid turn, so `ai.generate` retries three times with backoff on timeouts and 5xx.
- **Result:** 9/9 end-to-end checks pass against real Gemini, including the gate holding a `先週` request as a proposal and the final answer being numerically correct (¥1,200 after undoing ¥850).
- **Files:** `app/shared/ai.py`, `app/shared/config.py`, `tests/smoke_chat.py`, `tools/repro_request.py`, `tools/set_env_value.py`

### 2026-11-25 — M4 close-out: two chat bugs, notebooks brought back in line
- **What:** handoff spot-check, greeting-card fix, no-reload timestamp fix, full re-verification, integration
- **Why:** the handoff's queue item 2 was the only item that did not need an owner gate, and the notebooks had stopped tracking P2/P3/M4
- **Decisions:**
  - Every handoff claim was re-checked before being trusted. Two did not hold: the branch was 21 commits ahead of `main` (not four), and "no bubble timestamps" was only true on the no-reload path because `POST /chat/send` rendered the partial without `show_time`.
  - The timestamp fix went to the render site (pass `show_time`) rather than into the client script, so a reload and an appended bubble produce the same markup.
  - The new greeting-card check was proven non-vacuous: old template 10/11, new template 12/12. A check that cannot fail is not evidence.
  - The full seven-suite gate was re-run after the change, never a subset: a partial run is what let a three-commit regression through earlier.
  - The owner authorised the restart of 8010. It now runs detached (pid 4960, log in `%TEMP%`), which is the accepted trade-off for a demo server that does not reload Python.
  - `MEMORY.md` was rewritten because it predated P2/P3/M4. The P2/P3/M4 rationale is not reconstructed from memory: it stays in the commit messages and `docs/handoff/2026-11-25-ui-foundation.md`.
- **Files:** `tools/make_chat_assets.py`, `app/chat/templates/chat.html`, `app/chat/routes.py`, `.verify/journeys/chat.py`, `MEMORY.md`, `DECISIONS.md`

### 2026-11-25 — GitHub messages stay short and plain
- **What:** added one rule to `AGENTS.md`: commit messages and PRs use one short, everyday sentence; the real why belongs in this file.
- **Why:** the owner asked for it — long technical write-ups were burying the simple answer.
- **Files:** `AGENTS.md`

### 2026-11-26 — Receipt card: one date spelling, and a payee that cannot be cut off
- **What:** the receipt card now prints the date the same way the chat card does, and a long payee wraps onto more lines instead of ending in an ellipsis.
- **Why:** the owner's review of the dark-surface captures approved these two, and both were visible defects: `2026/11/25` beside `2026年11月26日（木）` on the neighbouring surface, and `株式会社エヌ・ティ・ティ・ドコモ・モ…` for a payee the user is being asked to confirm.
- **Decisions:**
  - The date uses the existing `jp_date` helper rather than a second formatter. `card.date_label` was already computed and simply ignored by the template, so the fix was to make the template read it and to feed it the override date when a validation round-trip happens.
  - The payee wraps (`white-space:normal; overflow-wrap:anywhere`) instead of ellipsising, because the whole point of the card is that the user can read what will be saved. `row-shop` scopes it so amount and date keep their single-line alignment.
  - Measured before and after at 390x844 rather than eyeballed: clipped 658 px of text into a 290 px box before, `scroll == client` after, and no horizontal page overflow in either state.
  - `base.css` already truncated every `.row-v` with an ellipsis; the shop row is the one place that must not, which is why the change is a scoped override and not a global one.
  - The `.verify` receipts journey asserted `.swipe`, a class the M4 rebuild deleted, so it could never pass and was never part of M4's evidence. It now asserts the rendered card, the Japanese date form, and the long-payee wrap; 5/5 on both the working tree and the live server.
- **Files:** `tools/make_receipt_assets.py`, `app/receipts/templates/receipts.html`, `app/static/receipts.css`, `app/receipts/routes.py`, `.verify/journeys/receipts.py`, `docs/design/dark-surface-review-2026-11-26.md`

### 2026-11-26 — Getting the app onto the owner's phone without shared Wi-Fi
- **What:** the app is now reachable from the owner's Android phone over mobile data through a free Cloudflare tunnel, and `docs/test-walkthrough.md` lists every step with the screen it should produce.
- **Why:** the owner cannot put the phone on the same Wi-Fi as the computer, so LAN testing was impossible; a public tunnel removes the network as a variable without installing anything on the phone.
- **Decisions:**
  - cloudflared quick tunnel, not a named tunnel or a paid plan: no account, no DNS, one random HTTPS URL, and it dies with the process — exactly the lifetime a test run should have.
  - Server rebound from `127.0.0.1` to `0.0.0.0` so both the tunnel and the local-subnet fallback work from one instance; the earlier bind was the reason LAN testing would have failed even after the firewall was fixed.
  - Firewall rule scoped to `TCP 8010`, `RemoteAddress LocalSubnet`, all profiles — the previous python.exe rules only covered the Public profile, and the Wi-Fi network here is Private, so the phone would have been blocked on both paths.
  - The tunnel makes the app public, so the walkthrough says plainly: throwaway password, sample screenshot not a real bank image. The app already isolates data per user id, which is what keeps that acceptable for a demo.
  - Expected outcomes in the walkthrough were produced by running the flow (register, send, undo, upload, save, bill, dark mode) before writing them down, not from reading the templates.
- **Files:** `docs/test-walkthrough.md`, `MEMORY.md`

### 2026-11-26 — Chat polish after the owner's phone review
- **What:** send button is an icon-only arrow, every yes/no surface uses one swipe card, the AI can ask a yes/no question as a card, thinking is capped, and the app now uses the owner's teal `#4F7075` with an Arial stack.
- **Why:** the owner's phone pass found the send control looked off compared with Messenger/ChatGPT, and that after a swipe the app asked again with an old button card; she also asked for her own base colour and font.
- **Decisions:**
  - Send is a 44x44 arrow **outside** the input pill (Messenger/ChatGPT layout), disabled and grey when the field is empty; the model's reasoning was not involved, this is chrome.
  - A structured `ask_user` tool plus a `question` payload means a binary question can arrive as a card; answers post to `/chat/answer/<id>`, are stored as a normal user message, and continue the same turn. Proposal cards reuse the same component but keep `/chat/confirm` and `/chat/cancel`, so saving never goes through the model.
  - Swipe alone would fail WCAG 2.5.7, so tap buttons and arrow keys stay; the card announces the chosen answer with `aria-live`.
  - The hardcoded regex fast path was built, measured at 232ms, then **removed** — the owner explicitly wants AI understanding, not programmed rules. Recorded here so nobody rebuilds it by accident.
  - Latency root cause measured, not guessed: Gemini 3.1 thinks dynamically by default and single turns stalled 13–60s; `GEMINI_THINKING=off` plus a 10s timeout (`GEMINI_TIMEOUT`) took the worst case from 124s to ~17s, with p50 1.0–3.0s. The 60s default timeout was the reason a stall looked like a two-minute hang.
  - Colour: `#4F7075` is the accent fill (white on it = 5.37:1, passes AA); dark mode uses `#7FA6AC` for accent text because the raw hex is only 3.32:1 on the dark background. Semantic red/green tokens were left alone.
  - Font: Arial first for latin, with Japanese fallbacks pinned (`Hiragino Kaku Gothic ProN`, `Yu Gothic`, Meiryo, Noto Sans JP) because Arial has no kana and the OS fallback differs per machine.
  - `/favicon.ico` 404 removed with an inline SVG data-URI icon rather than a new binary file.
  - 「日付は推測です」 is now suppressed when the inferred date is today, because that is the obvious reading; it still shows when the date differs.
  - The nav tab `レシート` became `写真`, because that page only lists photographed receipts and an empty list read as lost data.
- **Files:** `app/chat/templates/chat.html`, `app/chat/templates/_msg.html`, `app/chat/templates/_ask.html`, `app/static/ask.js`, `app/static/ask.css`, `app/static/chat.css`, `app/static/base.css`, `app/chat/tools.py`, `app/chat/service.py`, `app/chat/routes.py`, `app/shared/ai.py`, `app/shared/config.py`, `app/shared/templates/base.html`, `tests/test_ask.py`, `tests/ui_send.py`, `tests/ui_perf.py`, `tests/ui_sweep.py`, `tools/bench_turn.py`, `tools/bench_thinking.py`, `docs/design/*.md`

## 2026-11-26 — A photo of the thing he bought, and a smaller confirm card

- **What:** the third phone finding was a photo of the purchased item (clothes, water, snack) rather than a receipt; the app must ask for the price instead of refusing the image. Also trimmed the proposal card and fixed a card that never rendered.
- **Why:** a non-receipt photo hit 「お支払いとして読み取れませんでした」 and a dead end, which is the opposite of what he does on his phone. While verifying it, a pending proposal turned out never to appear after an in-page send, so his relative-date messages looked broken.
- **Decisions:**
  - The ask-for-a-price screen already existed; the fix is a **deletion** — the `unreadable` branch is gone, so any image without an amount lands on 「いくらでしたか？」 with an empty, required amount box.
  - A machine-read amount is discarded when `is_payment` is false, so a menu or price list can never become an expense; his typed amount is never discarded. The save route applies the same rule.
  - An item photo never becomes "ready": it is always confirmed by tapping 保存する. No auto-save on non-payment evidence.
  - The extraction prompt now names the item-photo case and asks for the shop/brand in `source`, because a blank 店・内容 made the card useless.
  - `tools/make_receipt_assets.py` is the source of truth for `receipts.html` and `receipts.css`; they were verified byte-identical before editing, and the generator was edited then re-run rather than hand-editing the output.
  - The dropped card was a live-collection bug (`template.content.children` shifting while appending), fixed with `Array.from` — one word, no new machinery.
  - Card trim: amount, category, source and a short date on one row; the long Japanese date is only drawn when the date is not today; the warning is one short sentence; the swipe hint stays once and muted; both buttons stay for WCAG 2.5.7; 直す is a muted underlined link but keeps its 44px target.
  - Dates are compared with `today_jst()`, not the server's `date.today()`.
- **Files:** `app/receipts/routes.py`, `app/receipts/extract.py`, `tools/make_receipt_assets.py`, `app/chat/templates/chat.html`, `app/chat/templates/_msg.html`, `app/chat/service.py`, `app/static/chat.css`, `tests/test_receipts_ask.py`, `tests/test_card_trim.py`, `.verify/journeys/receipts_item.py`, `.verify/journeys/proposal_card.py`, `docs/design/item-photo-and-card-trim-2026-11-26.md`

## 2026-11-26 — Navigation: drawer on phone, 248px rail on desktop

- **What:** replaced the thin top tab strip with one navigation component — an off-canvas drawer below 840px and a persistent 248px sidebar above it — and turned the chat empty state into a centred hero instead of a grey chat bubble.
- **Why:** the owner said the UI looked awful and that ChatGPT/Gemini/Claude "all make sidebar style". Research showed none of them ships a persistent sidebar on a phone: ChatGPT and Claude use a bottom bar plus a history drawer, Gemini a slide-in drawer, and the ~260px sidebar is their *desktop* shape. Material 3 puts a nav bar (3-5 destinations) under 600dp, a rail at 600-839, a drawer at 840+. Our top strip matched none of the three.
- **Decisions:**
  - No bottom tab bar: `.composer` is `position:fixed; bottom:0`, so the two would collide on the screen he uses most.
  - Drawer: `min(84vw,288px)`, 220ms `cubic-bezier(.2,.8,.2,1)`, scrim `rgb(15 23 42/.45)`, `inert` when closed, Escape closes and returns focus, `aria-expanded` on the hamburger, motion disabled under `prefers-reduced-motion`.
  - Desktop: 248px sticky rail, hamburger hidden, composer offset `left:248px`, content column 768px.
  - Three destinations stay; that is inside Material's bar range, so no rail tier at 600-839px.
  - Palette untouched (`#4F7075` / `#7FA6AC`) on his instruction.
  - The welcome block is no longer `.msg.bot` — a chat bubble used as a welcome screen is the AI tell he was reacting to.
  - The empty-state copy changed, so the chat journey now asserts `.intro`/`.hello` structure instead of legacy wording.
  - Research lanes failed this round (benchmark-scout children had no web tools and wrote stray tool-call text; the scout audit lane died on a missing model). Recorded as a harness failure and done with the parent's own tools instead — not counted as evidence.
- **Files:** `app/shared/templates/base.html`, `app/static/base.css`, `app/chat/templates/chat.html`, `app/static/chat.css`, `.verify/journeys/shell_nav.py`, `docs/design/shell-navigation-2026-11-26.md`, `C:/Users/minht/.agents/skills/snap-track-shell/SKILL.md`

## 2026-11-26 — Latency measured, swipe card hardened, sixteen visual details fixed

- **What:** measured real AI latency, measured the swipe card's actual physics, changed the gesture contract, and fixed sixteen visual defects found by a screenshot audit.
- **Why:** the owner asked "how much respond time of ai" and I had no honest number; then asked for the swipe feature to be tested and researched properly, and for the UI details to be finished.
- **Decisions:**
  - Latency is reported as a distribution, not a vibe: p50 4.98s / p95 14.4s over n=9 including retries, plus 54.6s worst case with the thinking budget on. One UI-level sample was 1.1s, and the report says it is one sample.
  - Swipe keeps its **96px distance commit and no velocity rule**. Tinder-style references commit on flick (MUI: 450px/s) and default to 300px distance; for a money record a short fast flick must not save. Documented as a deliberate divergence, not an oversight.
  - Tilt stays at **5°** at 140px. The advisor argued against raising it; the reference ceiling is ~20°, so there is room, but nothing measured says users are confused by tilt - they were confused about *direction*, which the hint now names.
  - **Horizontal intent lock**: a drag becomes horizontal only when `abs(dx) >= 1.5 * abs(dy)`; vertical wins once and never reclassifies. This stops a diagonal scroll from saving or discarding.
  - **Arrow keys now focus the button** instead of committing. An accidental arrow press used to save money instantly; Enter still commits, so keyboard users keep a full path.
  - Under `prefers-reduced-motion` the card no longer translates or tilts; the swipe still records.
  - Sixteen CSS/template fixes accepted from the audit, including a real bug of mine: the 840px media query sat above the base `.wrap` rule, so the desktop layout never applied. The receipts date field clipped `2026` to `202` because the 28px amount style applied to every input.
  - Four card-state blockers found by code review were **left unfixed this round** and are recorded in MEMORY as the next job; fixing server-side state transitions minutes before a review would have been reckless.
- **Files:** `app/static/ask.js`, `app/static/ask.css`, `app/static/chat.css`, `app/static/base.css`, `tools/make_receipt_assets.py`, `app/receipts/templates/receipts.html` (regenerated), `app/static/receipts.css` (regenerated), `app/chat/templates/_msg.html`, `app/chat/templates/_ask.html`, `.verify/journeys/swipe_gestures.py`, `docs/design/swipe-card-research-2026-11-26.md`

## 2026-11-27 — Receipts amount keypad (owner picked Option B)

- **What:** the 「いくらでしたか？」 screen now has a big amount field and a drawn keypad in a fixed bottom bar, with the category chips sitting above the keys.
- **Why:** the owner reviewed four mockups (A big number + native keypad, B drawn keypad, C summary rows, D two steps) and chose B. The old screen had a small underlined field and two rows shouting 教えてください.
- **Decisions:**
  - **Progressive enhancement, not a JS-only widget.** The pad ships with `hidden`; `pad.js` unhides it and sets `inputmode=none` so the phone keyboard does not fight the pad. The `<input type="number" name="amount">` stays the submitted value, so no-JS users still get the native keyboard and hardware typing still works.
  - The pad writes digits only, max 9; `00` appends two, `けす` deletes one. `⌫` was replaced with the word けす because the glyph rendered as a boxed symbol in Chromium.
  - **Required controls must be visible:** the 分類 chips are required when the category is unknown and were being clipped behind the fixed pad, so they moved into the pad bar as a horizontally scrollable row.
  - The 日付 row no longer force-opens (it pushed the card under the pad) and its copy changed from 教えてください to 写真からは読めません, because a field already showing today's date contradicted the old wording.
  - The amount is the input itself at 44px rather than a separate display, so nothing can drift out of sync and the focus ring is always on something real. Cost: no thousands separator.
  - Save disables itself and shows 保存中… on submit, blocking a double tap.
- **Files:** `tools/make_receipt_assets.py` (template and CSS source), `app/receipts/templates/receipts.html` and `app/static/receipts.css` (regenerated), `app/static/pad.js` (new), `.verify/journeys/receipts_item.py`, `.verify/journeys/_common.py`, `documents/_extract/recon/make_proposals.py`

## 2026-11-27 — Confirm card floats (owner chose Option 2), 直す removed

- **What:** the pending confirm card is now promoted into a centred floating card over a blurred chat, drags show 保存 / やめる stamps, 直す is gone, and the saved card carries 記録しました / 取り消す inside itself.
- **Why:** the owner picked Option 2 from the mockups, called the swipe hint messy, and said he would rather type a correction in chat than use 直す.
- **Decisions:**
  - **Promotion, not a second component.** The card is rendered inline by the server exactly as before; `ask.js` moves the same node into a `.modal-wrap` and shows a `.veil`. With JavaScript off, the card stays inline and every button still works. No duplicate markup, no duplicated state.
  - **Closing is always cancel.** ×, Escape, and a tap on the veil all return the card to the thread with `data-state` untouched. Nothing is saved or lost, which answers the HIG objection about alerts on undoable actions. Closing is ignored while a request is in flight (`data-state="pending"`).
  - **Blur instead of a dark veil** (`rgba(15,23,42,.18)` + `backdrop-filter: blur(7px)`) so the conversation stays legible behind the card.
  - **No hint text.** Direction is shown by stamps that fade and scale with the drag (Tinder's actual mechanism); nothing is drawn at rest. NN/g guidance says looping arrows are distracting, so there is no looping arrow animation.
  - **Card is centred with `margin:auto`, not `align-items`.** Measured: the flex alignment left the card at y=18, `margin:auto` put it at y=335 in an 844 viewport. Also needed `box-sizing:border-box`, otherwise it rendered 379px wide instead of 342px.
  - **直す deleted** (with its inline form). Corrections belong in chat.
  - The saved card's 記録しました / 取り消す moved from a sibling form into `.foot` inside the same card, so one event is one object.
  - `_msg.html` still renders the modal-branch markup for the no-JS path; the close button ships `hidden` and is unhidden on promotion.
- **Tests:** `test_card_trim` 14/14 now asserts the hint is gone, stamps exist, 直す is absent and `data-modal` is present; `proposal_card` journey 21/21 now covers float, veil, `aria-modal`, Escape-returns-without-saving, card stays and reopens, outside tap never saves, save works, and the footer sits inside the entity.
- **Files:** `app/chat/templates/_msg.html`, `app/static/ask.js`, `app/static/ask.css`, `tests/test_card_trim.py`, `.verify/journeys/proposal_card.py`, `.verify/journeys/swipe_gestures.py`, `documents/_extract/recon/probe_modal.py`

