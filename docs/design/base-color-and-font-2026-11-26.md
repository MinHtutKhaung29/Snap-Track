# Base color and font — spec (2026-11-26)

Owner request: "I want to use base color this `#4F7075` and `font-family: Arial, Helvetica, sans-serif;`".

Status: **specified, not applied** — no CSS changed yet. This file is the contract.

## 1. Color: `#4F7075`

RGB 79,112,117 — a muted teal. Measured contrast (WCAG 2.x, sRGB):

| pair | ratio | verdict |
|---|---|---|
| white on `#4F7075` | **5.37:1** | passes AA normal text |
| `#4F7075` on white | 5.37:1 | passes AA |
| `#4F7075` on dark bg `#0f172a` | **3.32:1** | fails AA normal text; ok only for large text / shapes |
| `#7FA6AC` on `#0f172a` | 6.76:1 | passes AA (dark-mode text tint) |

So one flat hex cannot serve both themes for text. Plan: `#4F7075` as the accent fill in both themes (white text on it), and `#7FA6AC` for accent text/links in dark mode only.

### Token changes in `app/static/base.css`

| Before | After | Why |
| --- | --- | --- |
| light `--accent:#2563eb` | `--accent:#4F7075` | owner's base color; white on it is 5.37:1 |
| light `--accent-press:#1d4ed8` | `--accent-press:#3f5a5e` | a darker step of the same hue, not a different hue |
| light `--accent-fg:#1d4ed8` | `--accent-fg:#3f5a5e` | links need 4.5:1 on white; this is 6.26:1 |
| light `--pick-bg:#dbeafe` / `--pick-fg:#1d4ed8` / `--pick-dot:#2563eb` | `#e3edee` / `#33565a` / `#4F7075` | tinted selection must stay on-hue with the accent |
| dark `--accent:#2f6fe8` | `--accent:#4F7075` | fills keep white text at 5.37:1 |
| dark `--accent-fg:#60a5fa` | `--accent-fg:#7FA6AC` | 6.76:1 on `#0f172a`; the raw hex would be 3.32:1 |
| dark `--pick-bg:#172554` / `--pick-fg:#dbeafe` / `--pick-dot:#60a5fa` | `#1b2b2d` / `#cfe3e5` / `#7FA6AC` | selection reads on dark without glowing |

Untouched on purpose: `--ok`, `--ng`, `--warn`, `--err-*`, `--note-*`. Those carry meaning (saved vs error), and re-hueing them to the brand teal would delete the success/error signal.

## 2. Font

Requested: `Arial, Helvetica, sans-serif`.

The trap: **Arial has no Japanese glyphs.** With only that stack, 「ランチ 850円」 renders digits/latin from Arial and kana/kanji from a per-OS fallback, so glyph weight and baseline jump inside one bubble, and the result differs on Windows, macOS and Android. Implementation keeps Arial first for latin and pins the Japanese fallback explicitly:

```css
--font-ui: Arial, Helvetica, sans-serif, "Hiragino Kaku Gothic ProN", "Yu Gothic", "Yu Gothic UI", Meiryo, "Noto Sans JP";
```

| Before | After | Why |
| --- | --- | --- |
| `body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,"Hiragino Sans",…}` | `body{font-family:var(--font-ui)}` | owner's requested stack, with the Japanese fallback pinned instead of left to the OS |
| form controls using `font-family:inherit` | same, but now inherit `--font-ui` | controls do not inherit body font by default; keep the explicit inherit |
| `line-height:1.7` | unchanged, verify at 390px | Arial's tighter default metrics change the perceived spacing; only adjust after a screenshot |

Arial digits are tabular by default, which helps amounts line up; `font-variant-numeric:tabular-nums` already on the status list stays.

## 3. Files to touch

- `app/static/base.css` — token blocks (light + dark), `body` font stack, form-control font reset. No template or JS change.

## 4. Verification (before claiming done)

1. Capture 390×760 and 1280×800, light and dark: chat with ask card + proposal card, receipts, commitments, login.
2. Re-measure contrast from the rendered page, not from this table.
3. Check accent-bearing parts specifically: send arrow fill, swipe-card buttons, active tab underline, focus rings, selection tint.
4. Confirm a mixed bubble (latin + Japanese) shows no size/baseline jump.

## 5. Open questions

- Is `#4F7075` the **accent** (buttons, links, active tab) or the page background? This spec assumes accent; a teal page background changes every pair above.
- Dark mode: accept `#7FA6AC` for accent text, or keep `#4F7075` everywhere and accept 3.32:1 (fails AA for body text)?
