import json
import os
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "documents", "_extract", "ui-sweep")
BASE = os.environ.get("BASE", "http://127.0.0.1:8010")
HEADED = os.environ.get("HEADED", "1") == "1"
EMAIL = os.environ.get("SWEEP_EMAIL", "live-watch-20261126@example.com")
PASSWORD = os.environ.get("SWEEP_PASSWORD", "watch-me-123")

report = {"steps": [], "console": [], "failed_requests": [], "frames": {}}


def shot(page, name):
    page.screenshot(path=os.path.join(OUT, name + ".png"))


def frames(page, ms=900):
    return page.evaluate(
        "(ms) => new Promise(done => { const t = []; const start = performance.now();"
        " const tick = now => { t.push(now); if (now - start < ms) requestAnimationFrame(tick); else done(t); };"
        " requestAnimationFrame(tick); })",
        ms,
    )


def stats(samples):
    gaps = sorted(round(b - a, 1) for a, b in zip(samples, samples[1:]))
    if not gaps:
        return {"n": 0}
    return {"n": len(gaps), "p50": gaps[len(gaps) // 2], "p95": gaps[min(len(gaps) - 1, int(len(gaps) * 0.95))], "max": gaps[-1]}


def step(page, name, fn):
    start = time.time()
    ok, note = True, ""
    try:
        fn()
    except Exception as exc:
        ok, note = False, type(exc).__name__ + ": " + str(exc)[:140]
    report["steps"].append({"step": name, "ok": ok, "ms": round((time.time() - start) * 1000), "note": note})
    print(("PASS " if ok else "FAIL ") + name + ("  " + note if note else ""))


def open_nav(page):
    button = page.locator("[data-drawer-toggle]")
    if button.count() and button.is_visible():
        button.click()
        page.wait_for_timeout(320)


def login(page):
    page.goto(BASE + "/login", wait_until="networkidle")
    page.fill('input[name="email"]', EMAIL)
    page.fill('input[name="password"]', PASSWORD)
    page.click('.form button[type="submit"]')
    page.wait_for_url("**/chat", timeout=20000)


def toggle_details(page, opening):
    summary = page.locator("summary")
    if summary.count() == 0:
        print("SKIP details, none on this page")
        return
    element = summary.first
    if element.evaluate("el => el.parentElement.open") != opening:
        element.click()
    page.wait_for_timeout(300)


def main():
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not HEADED, args=["--window-position=120,40"] if HEADED else None)
        context = browser.new_context(viewport={"width": 390, "height": 740}, locale="ja-JP")
        page = context.new_page()
        page.bring_to_front()
        page.on("console", lambda m: report["console"].append({"type": m.type, "text": m.text[:160]}) if m.type == "error" else None)
        page.on("requestfailed", lambda r: report["failed_requests"].append({"url": r.url[:110], "why": str(r.failure)[:60]}))

        step(page, "login", lambda: login(page))
        shot(page, "fast-01-chat")
        report["frames"]["chat"] = stats(frames(page))

        step(page, "tab-photo", lambda: (open_nav(page), page.click('.nav a[href="/receipts"]'), page.wait_for_load_state("networkidle")))
        shot(page, "fast-02-photo")
        report["frames"]["photo"] = stats(frames(page))

        step(page, "tab-commitments", lambda: (open_nav(page), page.click('.nav a[href="/commitments"]'), page.wait_for_load_state("networkidle")))
        shot(page, "fast-03-commitments")
        report["frames"]["commitments"] = stats(frames(page))

        step(page, "tab-chat", lambda: (open_nav(page), page.click('.nav a[href="/chat"]'), page.wait_for_load_state("networkidle")))
        step(page, "open-details", lambda: toggle_details(page, True))
        shot(page, "fast-04-details")
        step(page, "close-details", lambda: toggle_details(page, False))

        step(page, "send-disabled-check", lambda: page.wait_for_function("() => document.querySelector('#send-btn').disabled === true"))
        step(page, "composer-focus", lambda: (page.click('[name="message"]'), page.wait_for_timeout(250)))
        shot(page, "fast-05-focus")

        step(page, "logout", lambda: (open_nav(page), page.click('.side-foot button:has-text("ログアウト")'), page.wait_for_url("**/login", timeout=15000)))
        shot(page, "fast-06-login")
        context.close()

        dark = browser.new_context(viewport={"width": 390, "height": 740}, locale="ja-JP", color_scheme="dark")
        page = dark.new_page()
        step(page, "dark-login", lambda: login(page))
        shot(page, "fast-07-dark-chat")
        report["frames"]["dark-chat"] = stats(frames(page))
        dark.close()
        browser.close()

    with open(os.path.join(OUT, "report-fast.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=1)
    print(json.dumps(report["frames"], ensure_ascii=False))
    print("console_errors=%d failed_requests=%d steps=%d fails=%d"
          % (len(report["console"]), len(report["failed_requests"]), len(report["steps"]), sum(1 for s in report["steps"] if not s["ok"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
