# Chat UI spec (evidence-based)

Purpose: replace the current "form-dump in a chat costume" with a layout copied from apps that have solved it. Every number below is either read directly out of a repository or measured; opinions are labelled.

Status: **part 1 (tokens, geometry, bubbles) read first-hand from source.** Parts 2-4 are being researched and will be appended.

---

## 1. Where the numbers come from

| source | how read | what it gave |
|---|---|---|
| `Ajaxy/telegram-tt` — `src/styles/themes.json` | `gh api` → base64 → read | full light/dark colour token pairs |
| `Ajaxy/telegram-tt` — `src/styles/index.scss` | same | `--border-radius-messages: 1rem`, `--border-radius-messages-small: 0.5rem` |
| `Ajaxy/telegram-tt` — `src/components/middle/message/Message.scss` | same | bubble `--max-width: 29rem`, per-corner radius, grouping collapse under 600px |
| `Ajaxy/telegram-tt` — `src/styles/_spacing.scss` | same | 4px-step spacer scale (0.25rem increments), i.e. 4 / 8 / 16 / 24 / 32 |
| Apple HIG, WCAG 2.2, Japan DADS | published | 44pt targets, 4.5:1 contrast, 16px minimum body, 170% line-height for Japanese |

Telegram Web A is the only major chat product that publishes real CSS tokens; LINE, WhatsApp, iMessage, Slack and Discord do not publish consumer layout specs. Where a number is not from source it is marked.

---

## 2. Colour tokens

Telegram's own values, as a light/dark pair, for reference:

| token | light | dark |
|---|---|---|
| primary (accent) | `#3390EC` | `#8774E1` |
| background | `#FFFFFF` | `#212121` |
| background-secondary | `#F4F4F5` | `#0F0F0F` |
| background-own (outgoing bubble) | `#E1FFC7` | `#766AC8` |
| text | `#000000` | `#FFFFFF` |
| text-secondary | `#404040` | `#AAAAAA` |

Two things worth copying literally, because they are the reason it reads as a real product rather than a template:

1. **The outgoing bubble is tinted, not the brand colour.** Outgoing is a soft green in light mode (`#E1FFC7`), not Telegram blue. Blue is reserved for links, buttons and selection.
2. **Dark mode is not an inversion.** Background drops to near-black (`#212121`), the secondary surface goes *darker* than the background (`#0F0F0F`), and the accent shifts hue (blue → violet) because saturated blues vibrate on dark.

Our own palette, same structure, keeping the app's blue and the money-specific semantics:

```css
:root{
  --accent:#2563eb;
  --bg:#ffffff;
  --surface:#f4f5f7;
  --bubble-in:#f1f3f7;
  --bubble-out:#e3efff;
  --text:#0f172a;
  --text-muted:#5b6472;
  --line:#e3e7ee;
  --money-in:#0f766e;
  --warn:#b45309;
}
@media (prefers-color-scheme: dark){
  :root{
    --accent:#7c9cff;
    --bg:#14161a;
    --surface:#0e0f12;
    --bubble-in:#1c1f26;
    --bubble-out:#1e2a44;
    --text:#e8ecf3;
    --text-muted:#9aa4b2;
    --line:#262b33;
    --money-in:#5eead4;
    --warn:#fbbf24;
  }
}
```

Rules: one accent. No gradients. Money sign carries the meaning (`−¥1,234` / `+¥50,000`); colour only reinforces, never alone (WCAG 1.4.1).

---

## 3. Type and spacing

| role | size | line-height | weight |
|---|---|---|---|
| amount hero | 34px | 1.1 | 700, tabular figures |
| page title | 15px | 1.2 | 600 |
| bubble body | 16px (Japanese) / 15.5px latin | 1.65 | 400 |
| list row value | 15px | 1.3 | 500 |
| label / meta | 13px | 1.3 | 400, muted |
| timestamp | 11.5px | 1.2 | 400, muted |

Japanese body text needs 16px minimum and ~170% line-height (Japan DADS), so a bubble that holds Japanese must not go below 16px. Spacing uses the 4px scale only: 4 / 8 / 12 / 16 / 24 / 32.

---

## 4. Bubbles

| property | value | source |
|---|---|---|
| radius | 16px (`1rem`) | telegram `index.scss` |
| grouped corner | 8px (`0.5rem`) | telegram `Message.scss` |
| max width | 29rem = **464px** desktop, **78%** of viewport on mobile | telegram `Message.scss` + messenger consensus |
| padding | 12px 14px | telegram spacing scale |
| gap inside a group | 2-4px | messenger consensus |
| gap between groups | 8-12px | messenger consensus |
| timestamp | inside the last bubble of a group, 11.5px, muted | telegram `MessageMeta` |

Current build: 16px radius, 4px tail, 88% width. Radius is right; the width and grouped corner are wrong.

---

## 5. Composer

- Full-width bar; inner field is a **pill**, radius 20px, min height 44px.
- Send is a circular 44px button, accent-filled only when there is text.
- Attachment (📷) sits inside the left edge of the pill, not floating above the bar.
- Grows to 5 lines, then scrolls internally; never pushes send off-screen.
- Sits above `env(safe-area-inset-bottom)` and tracks the on-screen keyboard (part 4).

Current build floats the camera as a circle above the bar, which reads as an add-on rather than part of the input.

---

## 6. What we copy, what we ignore

**Copy:** tinted outgoing bubble; 16px radius with one collapsed corner per group; 464px max bubble width on desktop; 4px spacing scale; muted metadata inside the bubble; pill composer with inline attachment; accent reserved for interactive elements.

**Ignore:** Telegram's virtualised list and scroll anchoring (we render a small thread server-side); reactions; read receipts; thread panels; the three-column desktop layouts of Slack/Discord/Teams — a single-column app gains nothing from a sidebar it does not have.

---

## 7. Application checklist for this repo

1. `app/static/base.css` — palette from §2, type scale from §3, dark mode via `prefers-color-scheme`.
2. `tools/make_chat_assets.py` — 16px bubbles, grouped tail, 78% width, timestamp inside the last bubble, pill composer with inline 📷, thinking indicator as a bot bubble.
3. `tools/make_receipt_assets.py` — 34px tabular amount hero, summary rows instead of stacked fields, 96px thumbnail, blue primary, demoted destructive.
4. `tools/make_commitment_assets.py` — same row language; due rows louder than paid rows.
5. Capture every surface in **both** light and dark before calling it done.

---

## 8. Pending, and what research actually produced

- **Part 3 — not delivered.** The LINE / WhatsApp / iMessage / Slack / Discord / Teams / ChatGPT / Claude comparative lane timed out after 30 minutes and produced nothing usable. Not retried on purpose: part 1 stands on first-party source plus Apple HIG, WCAG 2.2 and Japan DADS, which is stronger than a digest of screenshots. Only the messenger *consensus* numbers in §4 (78% width, 2-4 / 8-12px gaps) are second-hand, and they are labelled as such.
- **Part 2 — outstanding.** Desktop column layout from Mattermost / Rocket.Chat / Signal Desktop / Zulip was blocked by the Antigravity Claude/GPT quota window (0% for ~4h). It only matters if this app ever grows a sidebar, which the plan does not call for.
- **Part 4 — returned.** The smoothness sheet is grounded in this repo's real selectors and marks three claims it could not verify on 2026 browsers. Two findings are directly actionable:
  1. `app/chat/templates/chat.html` pins the composer with `bottom:0` and has **no keyboard inset**, so on iOS the composer can sit under the keyboard. The 2026 fix is the viewport token `interactive-widget=resizes-content` (Chrome/Android confirmed on MDN; iOS unverified — needs a `visualViewport` JS fallback).
  2. The unverified claims each carry a fallback: iOS Safari `interactive-widget`, `navigator.vibrate`, `overflow-anchor`.
- **Provenance note.** In `Ajaxy/telegram-tt` the runtime source of truth is `theme.ts` / `DESIGN.md`, not `themes.json` — four legacy tokens differ between them, and server-provided chat themes can override `--message-*` and `--color-primary` at runtime.
