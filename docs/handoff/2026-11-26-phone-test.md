# Handoff — 2026-11-26 · owner's phone acceptance pass

## Mission anchor (verbatim; do not paraphrase)

- Goal: A Japanese graduation project — a spending tracker where the user types or photographs a payment in chat and gets a confirmed record.
- Master plan: `docs/base-plan.md`
- Docs / links: `docs/design/chat-ui-spec.md` · `docs/handoff/2026-11-25-m4-close.md` (previous phase) · `docs/test-walkthrough.md` (this phase's owner script) · `docs/design/dark-surface-review-2026-11-26.md` (this phase's evidence) · `MEMORY.md` · `DECISIONS.md`
- Current milestone: M4 — every surface (chat, receipts, commitments) passes its suite, renders correctly in light and dark at 390x844, and a photographed payment screenshot becomes a persisted record carrying amount, date and recipient. **Status: met, merged as `a235733`, and now open to the owner's phone for acceptance.**
- Non-goals / hard constraints: no monthly-summary work unless the owner asks; no 住居費 category unless the plan is amended; never edit `main` directly (branch + PR); do not kill the process on port 8011 without the owner's word; nothing here is a school deliverable deadline.

## Where things stand

- `main` = `origin/main` = `a235733`. PR #4 merged. Working tree has only: `M DECISIONS.md`, `M MEMORY.md`, `?? docs/test-walkthrough.md` — deliberately uncommitted, the owner has not asked for a docs commit.
- The owner is testing on an Android phone over mobile data and cannot join this computer's Wi-Fi.

## Running processes (survive a session replacement, die with the machine)

| what | address | pid |
|---|---|---|
| app server, merged code, bound to all interfaces | `0.0.0.0:8010` | 23516 |
| Cloudflare quick tunnel → `127.0.0.1:8010` | public HTTPS | background task of the previous session, `cloudflared.exe` pids 6420 / 11796 / 10272 |
| static evidence viewer (theme captures) | `127.0.0.1:18081` | 18564 |
| stray old-code instance — **leave alone, owner's call** | `127.0.0.1:8011` | 20668 |

Public test URL in use: `https://contribute-kinase-afford-riding.trycloudflare.com` (verified 200 on `/health`, `/login`, `/static/base.css`, and a full scripted flow).

Re-arm the tunnel if it dies (a new URL each time — read it off the log, then tell the owner the new one):

```
"C:\Users\minht\AppData\Local\Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\cloudflared.exe" tunnel --url http://127.0.0.1:8010 --no-autoupdate
```

Restart the app only if the Python changes (templates and CSS reload by themselves):

```
"C:\Users\minht\OneDrive\Desktop\snapandtrack\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8010 --app-dir .
```

Firewall rule already present: `Snap and Track 8010`, inbound TCP 8010, all profiles, `LocalSubnet` only.

## What this phase proved (evidence on disk)

- `receipts` journey **5/5** after merge, on the merged server — `documents/_extract/verify/20261126T015904Z-receipts`.
- Full scripted user flow through the **public tunnel**: register → chat card `−¥850` → undo → photo card `¥3,200 / 2026年11月25日（水）/ 東京電力エナジーパートナー` → save → empty state → bill card → commitments row → dark mode. Script: `documents/_extract/theme/_probe_flow.py`, `_probe_undo_bill.py`; screenshots `documents/_extract/theme/flow-*.png`.
- `contrast.py` ALL CHECKS PASS · `ui_image_forms` 11/11 · `test_extract` 6/6.

## Two findings the owner has not ruled on

1. **家賃 is filed under 光熱費.** The seed set has only 食費・交通費・日用品・交際費・光熱費・その他, so rent falls to the nearest. Adding 住居費 is a plan change, not a bug fix.
2. **Saving a receipt photo says nothing in the chat.** The card leaves the queue and the page shows its empty state; the transaction exists but the user gets no confirmation in the thread they were talking in. The base plan's original wording was "card flips, 元に戻す", so the intent was visible confirmation plus undo — the M4 rebuild dropped it for this path.

## Teaching state (owner-facing)

Concepts this phase put in the owner's hands, in plain words:

- **A session cookie is the login.** `SessionMiddleware` signs an opaque cookie with `secret_key`; nothing is stored server-side, so the browser carrying that cookie *is* the logged-in user.
- **`prefers-color-scheme` is a phone setting, not an app setting.** The app has no theme toggle; it asks the browser what the phone prefers. A light-looking app on a dark phone means Chrome reported light.
- **Localhost vs `0.0.0.0` vs a tunnel.** `127.0.0.1` answers only the same machine; `0.0.0.0` answers the whole local network; a tunnel gives the machine a public name. Each step widens who can reach the app, which is why the firewall rule is scoped to the local subnet and the public link carries a "throwaway password" warning.
- **Evidence means a run with an artifact, not a description.** Every "should see" line in `docs/test-walkthrough.md` came from a scripted run whose screenshots exist.

No new L2 explainer files were created this phase; the walkthrough itself is the teaching artifact.

## Next actions

1. **Wait for the owner's phone verdict.** Ask which steps misbehaved, in their words, before touching code. The walkthrough's step numbers are the shared vocabulary.
2. If the owner says "fix the chat confirmation", scope it as: after a receipt save, append one bot entry to the thread (`記録しました` + `取り消す`) using the existing chat partial and the existing undo endpoint — no new table, no new route shape.
3. If the owner says "add 住居費", that is a plan amendment first (`docs/base-plan.md` category table), then seeds, then category map — do not slip it in as a template tweak.
4. Commit the three uncommitted doc files on a branch (`docs/…`) only when the owner asks; never straight to `main`.
5. Keep the tunnel alive while testing; if it drops, re-arm, read the new URL from the log, and send the owner the new link rather than describing it.
6. Still unverified by anyone: the 8011 stray process's origin (it answers `/health` with `tables: 8`, so it is this app, old code). Ask before killing.
