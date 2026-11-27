# Shell navigation redesign (2026-11-26)

## What the owner said

> "i mean ui design not good. if you look at chatgpt, gemini, claude all make sidebar style i don't understand why you use that although i say do deep research on web and gh learn from pro designer ... clone it take it study learn make doc, install skill ... so try harder. do test, review"

Kept as instructed: the accent stays `#4F7075` / `#7FA6AC` (no palette change).

## 1. Research (web, with sources)

| Product | Phone (390px class) | Desktop |
|---|---|---|
| ChatGPT | **bottom tab bar** (Home / Explore / dot) **+ hamburger opens a sidebar drawer** for history ([OpenAI Help](https://help.openai.com/en/articles/20001723-using-the-new-experience-in-the-chatgpt-mobile-app)) | persistent left sidebar, ~260px, message column ~768px (`48rem`) |
| Claude | **bottom tab bar** (Chat / Projects / Code / Artifacts) **+ drawer for history** ([emergent.sh](https://emergent.sh/news/claude-mobile-app-gets-new-tab-bar-code), [Medium](https://medium.com/@zainab.asad/claude-for-android-gets-a-material-3-expressive-redesign-and-a-new-bottom-bar-30faa164e364)) | side panels up to ~45% of the viewport |
| Gemini | slide-in **navigation drawer** from a top-left hamburger or edge swipe ([sammyguru](https://sammyguru.com/google-adds-navigation-drawer-to-gemini-app-for-easier-access/)) | rail/drawer |

Material Design 3: a **navigation bar carries 3–5 destinations and is for compact windows (<600dp)**; **navigation rail** at 600–839dp; **navigation drawer** at 840dp+ ([nav bar](https://m3.material.io/components/navigation-bar/guidelines), [drawer](https://m3.material.io/components/navigation-drawer)).

**The finding that mattered:** none of the three ships a persistent sidebar on a phone. A 260px sidebar on a 390px screen would take two-thirds of the only screen he shoots and types on. Their "sidebar style" is a *desktop* shape and, on mobile, a drawer. Our old UI had neither — it had a thin top tab strip that no reference product uses, and it cost 44px of vertical space on a composer-driven screen.

GitHub research did not return usable output this round: both `benchmark-scout` lanes wrote 240 B and 459 B of stray tool-call text (no web tools inside that child), and the `scout` audit lane died with `Model "antigravity/gemini-4-hydrogen:low" not found`. That is a harness failure, not a research result; the numbers above come from the web sources and from reading our own files.

## 2. Decision

One navigation component, two modes — the same thing ChatGPT/Gemini do, adapted to a 3-destination app whose chat input is pinned to the bottom:

- **Below 840px:** the sidebar becomes an **off-canvas drawer** (max 288px, `min(84vw,288px)`), opened by a hamburger in the header, closed by scrim tap, by Escape, or by navigating. The composer stays untouched at the bottom — a bottom tab bar was rejected because `.composer` is `position:fixed; bottom:0` and the two would collide on the one screen he uses most.
- **At 840px and up:** a **persistent 248px sidebar** (ChatGPT's 260px minus a hair), content column capped at 768px, composer offset by the rail width.
- Exactly **3 destinations**, which is inside Material's 3–5 bar range and does not need a rail tier at 600–839px; the drawer simply becomes the rail at 840px.

## 3. Implementation (exact values)

| Piece | Value |
|---|---|
| Drawer width | `min(84vw, 288px)` |
| Slide | `transform` 220ms `cubic-bezier(.2,.8,.2,1)`, disabled under `prefers-reduced-motion` |
| Scrim | `rgb(15 23 42 / .45)`, 220ms `ease-out`, `pointer-events` none when closed |
| Rail | 248px fixed column, `min-height:100dvh`, `position:sticky` |
| Nav row | 44px min height, 10px radius, 20px inline SVG icon, 12px gap |
| Active row | `--pick-bg` surface + `--fg` text + accent icon, plus `aria-current="page"` |
| Closed drawer | `inert` (not focusable, not announced), `aria-expanded="false"` on the button |
| Open drawer | Escape closes and returns focus to the hamburger; scrim click closes |
| Header | hamburger only below 840px (`display:none` above) |
| Composer | `left:248px` at ≥840px so it clears the rail |
| Empty state | brand mark 40px, greeting 24px → `--t1` (34px) at ≥520px, muted lead, chips centred |

Files: `app/shared/templates/base.html`, `app/static/base.css`, `app/chat/templates/chat.html`, `app/static/chat.css`.

## 4. Review (looking at rendered pixels, not markup)

Strong now: the desktop view reads as a product — brand block, icon nav with an active pill, account pinned to the sidebar foot, content and composer aligned to the same column. The phone view is a chat screen with one 56px header bar and a centred hero, and no competing nav chrome.

Still weak, in priority order:

1. **The sidebar has a large dead zone** between the three items and the account row. ChatGPT fills it with conversation history; we have one thread per user (base plan), so there is nothing honest to put there yet. Filling it with fake content would be worse. Candidate: this month's total, which is already computed elsewhere.
2. **The header title duplicates the active nav item** on desktop (`チャット` twice). ChatGPT shows nothing there. Left in place because it is the page's `h1`; a visually-hidden `h1` on desktop is the fix if it bothers him.
3. **Sidebar empty dark hue:** the active pill uses `--pick-bg` (`#1b2b2d`, greenish) against the teal accent. Legible, but a hue step off the accent.
4. **Chips are still generic outline pills.** Pro apps style suggestion chips as quiet filled surfaces. Cosmetic, next pass.

## 5. Evidence

Suites, working tree, 2026-11-26: `test_ask` 38/38 · `test_gate` 15/15 · `test_confirm` 15/15 · `test_commitments` 16 OK · `test_extract` 6/6 · `test_receipts_ask` 13/13 · `test_card_trim` 12/12.

Journeys, 390x844 and 1280x800: `shell_nav` 24/24 (drawer opens/closes, scrim, Escape + focus return, inert, active state, navigation, desktop rail 248px at x=0, hamburger hidden, composer clears the rail, no horizontal overflow at either width) · `chat` 12/12 · `receipts` 5/5 · `receipts_item` 8/8 · `proposal_card` 12/12.

Screenshots: `documents/_extract/verify/20261126T165428Z-shell_nav-standalone/shots/` — `01-phone-closed.png`, `02-phone-drawer-open.png`, `03-phone-drawer-dark.png`, `04-desktop-chat.png`, `05-desktop-chat-dark.png`, `06-desktop-receipts.png`.

Baseline for comparison: `documents/_extract/verify/20261126T165254Z-shell_nav-standalone/shots/` holds the same views with the old top tab strip.

`tests/ui_sweep.py` broke on this change — it clicked `a[href="/chat"]` (now matching both the brand link and the nav row) and looked for a visible ログアウト that had moved into the drawer. Fixed in the tool: an `open_nav()` helper opens the drawer first and nav clicks are scoped to `.nav`. Re-run: 10/10 steps, `console_errors=0 failed_requests=0`, frames p50 16.7ms. The `chat` journey had also asserted the old empty-state sentence; it now asserts `.intro`/`.hello` structure rather than copy.

## 6. Not done (deliberately)

- No icon library added — three inline SVGs, per the project's no-new-dependency rule.
- No framework, no React, no CSS-in-JS: the drawer is 25 lines of vanilla JS.
- No conversation history list (there is one thread per user).
- No palette change, per his instruction.
