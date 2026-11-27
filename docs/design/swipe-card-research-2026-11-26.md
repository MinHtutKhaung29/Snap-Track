# The swipe card: how Tinder does it, what ours does (2026-11-26)

## 1. Measured behaviour of our card

Measured with `.verify/journeys/swipe_gestures.py` against the running app on :8010 (10/10 checks):

| Property | Ours | Measured how |
|---|---|---|
| Drag follows the finger | 140px drag → `translateX(140)` | computed matrix |
| Tilt at full pull | **5°** | `atan2(m12, m11)` |
| Tilt curve | `x / 140 * 5` degrees, capped by `CLAMP=140` | `ask.js:97` |
| Commit threshold | **96px**, distance only | `ask.js:2` |
| Start of a drag | 8px slop in either axis | `ask.js:4` |
| Spring-back under threshold | 60px → 4px → 0px within ~400ms | sampled at release, +70ms, +470ms |
| Buttons while posting | all disabled + `aria-busy` | `ask.js` `lock()` |
| Keyboard | ArrowLeft / ArrowRight answer the card | `ask.js:330` |
| Reduced motion | swipe still records, no fly-out animation | emulated `prefers-reduced-motion` |
| Double answer | blocked by `data-state` guard; one transaction per card | swipe + reload journey |

So the mechanics are sound: it follows the finger, springs back when you let go too early, saves exactly once, works with a keyboard, and respects reduced motion. The earlier suspicion that it "snaps back instantly" was wrong — my first probe never released the mouse.

## 2. How the reference implementations do it

| Source | Number | Meaning |
|---|---|---|
| `react-tinder-card` docs ([npm](https://www.npmjs.com/package/react-tinder-card)) | `swipeThreshold` **300px** in position mode | distance needed to commit; the docs warn 300px does not fit all screens and tell you to scale it |
| `react-swipeable` ([API](https://nearform.com/open-source/react-swipeable/docs/api)) | `delta: 10` | movement before a swipe is considered started |
| Material UI `SwipeableDrawer` ([API](https://mui.com/material-ui/api/swipeable-drawer/)) | `minFlingVelocity` **450 px/s** (tuning range 250–1000) | speed that counts as a deliberate flick |
| Tinder-style cards generally ([Medium teardown](https://medium.com/@amie.n.foster/swipe-it-like-its-hot-ad4d0882a97a), [React Native write-up](https://www.mariusreimer.com/blog/id/tinder-swipe-in-react-native/)) | tilt up to **~20°**, spring **0.3s** or tension 300 / friction 30 | what makes the gesture feel alive |

Tinder's own exact constants are not published; any specific "Tinder uses 120px" claim found in blogs is folklore and is marked unverified here.

## 3. Accessibility obligations

- **WCAG 2.5.1 Pointer Gestures**: anything done with a multi-point or path-based gesture needs a single-pointer alternative. Our card has two real buttons, so this is satisfied.
- **WCAG 2.5.7 Dragging Movements (AA)**: drag operations must work without dragging. Satisfied by the same buttons plus ArrowLeft/ArrowRight, which is stronger than required.
- **Consequence**: removing the buttons to make it "more Tinder" would break AA. The buttons stay.

## 4. Decisions

1. **Keep the 96px distance threshold and do not add velocity commit.** Tinder commits on a flick because a wrong choice costs nothing. Here a wrong swipe creates or discards a financial record, so a deliberate 96px drag (25% of a 390px screen) is the safer affordance. MUI's 450px/s fling would let a 30px flick save money — measured today: a 34px flick is correctly ignored.
2. **Raise the tilt from 5° to 12°.** 140px of drag currently produces almost no visual response. 12° is still well under the ~20° reference ceiling and reads clearly on a 390px screen.
3. **Show which choice the drag will produce.** This is the biggest comprehension gap: the card tilts but never says "this way is やめる / this way is 保存する". Tinder pairs motion with LIKE / NOPE overlays; chat apps pair swipe with a revealed action. Implement as a label that fades in on the side being pulled toward, reusing the existing button labels.
4. **Do not copy**: card stacking (one card at a time here), rewind/undo beyond the existing 直す + undo path, haptics (web support is unreliable), rotation beyond 20°.

## 5. What still needs a decision from the owner

- Whether the 96px threshold feels too long on a real thumb. It is measurable: anything under 96px silently springs back, which can read as "the app ignored me".
- Whether the drag label should name the action (やめる / 保存する) or the outcome (記録しない / 記録する).
