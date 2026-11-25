import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("VERIFY_PROJECT") or os.path.abspath(os.path.join(HERE, "..", ".."))
BASE = (os.environ.get("VERIFY_BASE_URL") or "http://127.0.0.1:8010").rstrip("/")
JOURNEY = os.path.splitext(os.path.basename(sys.argv[0]))[0]
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
RUN_DIR = os.environ.get("VERIFY_RUN_DIR") or os.path.join(
    ROOT, "documents", "_extract", "verify", STAMP + "-" + JOURNEY + "-standalone"
)
SHOTS = os.path.join(RUN_DIR, "shots")
VIDEO = os.path.join(RUN_DIR, "video")

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

results = []
console = []


def record(name, ok, detail=""):
    results.append({"check": name, "pass": bool(ok), "detail": str(detail)})
    print(("PASS " if ok else "FAIL ") + name + (("  " + str(detail)) if detail else ""))


def start_browser():
    from playwright.sync_api import sync_playwright

    os.makedirs(SHOTS, exist_ok=True)
    os.makedirs(VIDEO, exist_ok=True)
    pw = sync_playwright().start()
    browser = pw.chromium.launch()
    ctx = browser.new_context(
        viewport={"width": 390, "height": 844},
        device_scale_factor=2,
        is_mobile=True,
        has_touch=True,
        locale="ja-JP",
        record_video_dir=VIDEO,
        record_video_size={"width": 390, "height": 844},
    )
    page = ctx.new_page()
    page.set_default_timeout(120000)
    page.on("console", lambda m: console.append(m.type + " " + m.text))
    page.on("pageerror", lambda e: console.append("pageerror " + str(e)))
    return pw, browser, ctx, page


def shot(page, name):
    os.makedirs(SHOTS, exist_ok=True)
    path = os.path.join(SHOTS, name)
    page.screenshot(path=path, full_page=True)
    return path


def db():
    from app.shared import db as database

    return database


def email(which):
    return "verify-" + str(int(time.time())) + "-" + which + "@example.com"


def user_id(address):
    row = db().fetch_one("SELECT user_id FROM users WHERE email = %s", (address,))
    return row["user_id"] if row else None


def register(page, address, name="検証 太郎"):
    page.goto(BASE + "/register", wait_until="networkidle")
    page.fill('input[name="name"]', name)
    page.fill('input[name="email"]', address)
    page.fill('input[name="password"]', "verify-password-1")
    page.fill('input[name="password_confirm"]', "verify-password-1")
    page.click('.form button[type="submit"]')
    page.wait_for_url("**/chat", timeout=60000)
    page.wait_for_timeout(400)


def send(page, text):
    before = page.locator("#thread .msg").count()
    page.fill('[name="message"]', text)
    started = time.time()
    page.press('[name="message"]', "Enter")
    page.wait_for_timeout(120)
    bubbles = page.locator("#thread .msg.me")
    to_bubble = round((time.time() - started) * 1000)
    bubble = bubbles.last.inner_text() if bubbles.count() else ""
    page.wait_for_function(
        "(n) => { var f = document.getElementById('chat-form'); return f.dataset.busy === '0' "
        "&& document.querySelectorAll('#thread .thinking').length === 0 "
        "&& document.querySelectorAll('#thread .msg').length > n; }",
        arg=before,
        timeout=180000,
    )
    return bubble, to_bubble, round((time.time() - started) * 1000)


def receipt_photo():
    base = os.path.join(ROOT, "documents", "_extract", "p005", "real")
    for name in ("r02.jpg", "r01.jpg", "r03.jpg"):
        path = os.path.join(base, name)
        if os.path.exists(path):
            return path
    return ""


def finish():
    os.makedirs(SHOTS, exist_ok=True)
    passed = sum(1 for r in results if r["pass"])
    report = {
        "journey": JOURNEY,
        "app": os.environ.get("VERIFY_APP") or "snapandtrack",
        "stamp": STAMP,
        "base": BASE,
        "score": str(passed) + "/" + str(len(results)),
        "checks": results,
        "console": console,
    }
    with open(os.path.join(RUN_DIR, "report.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    with open(os.path.join(RUN_DIR, "console.log"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(console) if console else "(no console output)")
    print("")
    print("SCORE " + report["score"])
    print("console events: " + str(len(console)))
    print("evidence: " + RUN_DIR)
    return 0 if passed == len(results) else 1


def main(flow):
    pw, browser, ctx, page = start_browser()
    try:
        flow(page)
    except Exception:
        last = traceback.format_exc().strip().splitlines()[-1]
        record(JOURNEY + " ran to the end without an exception", False, last)
    finally:
        ctx.close()
        browser.close()
        pw.stop()
    sys.exit(finish())
