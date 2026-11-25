import os
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "documents", "_extract", "ui_images")
FIX = os.path.join(ROOT, "documents", "_extract", "fixtures")
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8010"
EMAIL = "img-" + str(int(time.time())) + "@example.com"
PW = "image-password-1"

from app.shared import db

results = []
console = []


def shot(page, name):
    path = os.path.join(OUT, name)
    page.screenshot(path=path, full_page=True)
    print("SHOT " + name + " " + str(os.path.getsize(path)))


def record(name, ok, detail=""):
    results.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + ("  " + str(detail) if detail else ""))


def uid(email):
    row = db.fetch_one("SELECT user_id FROM users WHERE email = %s", (email,))
    return row["user_id"] if row else None


def upload(page, path):
    if "/chat" not in page.url:
        page.goto(BASE + "/chat", wait_until="networkidle")
    page.set_input_files('input[name="photo"]', path)
    page.wait_for_url("**/receipts**", timeout=180000)
    page.wait_for_load_state("networkidle", timeout=120000)
    page.wait_for_timeout(400)


def main():
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True, locale="ja-JP")
        page = ctx.new_page()
        page.set_default_timeout(180000)
        page.on("console", lambda m: console.append(m.type + " " + m.text))
        page.on("pageerror", lambda e: console.append("pageerror " + str(e)))

        page.goto(BASE + "/register", wait_until="networkidle")
        page.fill('input[name="name"]', "画像 太郎")
        page.fill('input[name="email"]', EMAIL)
        page.fill('input[name="password"]', PW)
        page.fill('input[name="password_confirm"]', PW)
        page.click('.form button[type="submit"]')
        page.wait_for_url("**/chat", timeout=60000)
        uidv = uid(EMAIL)

        upload(page, os.path.join(FIX, "payment_screenshot.png"))
        body = page.content()
        shot(page, "01-screenshot.png")
        record("screenshot is accepted as evidence", "お支払いとして読み取れませんでした" not in body, "not rejected outright")
        has_amount = page.locator('input[name="amount"]').count() == 1
        record("amount field exists", has_amount)
        prefilled = page.input_value('input[name="amount"]') if has_amount else ""
        record("amount read from the screenshot, or asked for", prefilled == "3200" or prefilled == "", "prefilled=" + repr(prefilled))
        record("category chips are tappable options", page.locator('.chips label').count() == 6, "chips=" + str(page.locator('.chips label').count()))
        record("exactly one primary save", page.locator('.ask .primary').count() == 1, "primaries=" + str(page.locator('.ask .primary').count()))

        if not prefilled:
            page.fill('input[name="amount"]', "3200")
        page.locator('.chips label', has_text="光熱費").first.click()
        page.click('.ask button[type="submit"]')
        page.wait_for_load_state("networkidle", timeout=120000)
        page.wait_for_timeout(400)
        rows = db.fetch_all(
            "SELECT amount, source, category_id, source_kind FROM transactions WHERE user_id = %s AND deleted_at IS NULL",
            (uidv,),
        )
        record("saving the asked-about screenshot writes one row", len(rows) == 1 and int(rows[0]["amount"]) == 3200, rows)
        shot(page, "02-saved.png")

        upload(page, os.path.join(FIX, "not_payment.png"))
        body = page.content()
        shot(page, "03-not-payment.png")
        record("a non-payment image says so clearly", "お支払いとして読み取れませんでした" in body)
        record("offers manual entry", "手入力で登録" in body)
        record("offers retry", "もう一度とる" in body)

        page.goto(BASE + "/receipts?manual=1", wait_until="networkidle")
        record("manual entry shows the form", page.locator('input[name="amount"]').count() == 1)
        shot(page, "04-manual.png")

        page.goto(BASE + "/chat", wait_until="networkidle")
        page.locator('form[action="/logout"] button').first.click()
        page.wait_for_url("**/login", timeout=60000)
        stale = page.get_attribute('input[name="csrf_token"]', "value")
        page.fill('input[name="email"]', EMAIL)
        page.fill('input[name="password"]', PW)
        page.click('.form button[type="submit"]')
        page.wait_for_url("**/chat", timeout=60000)
        page.locator('form[action="/logout"] button').first.click()
        page.wait_for_url("**/login", timeout=60000)
        page.fill('input[name="email"]', EMAIL)
        page.fill('input[name="password"]', PW)
        page.evaluate("(t) => { document.querySelector('input[name=csrf_token]').value = t; }", stale)
        page.click('.form button[type="submit"]')
        page.wait_for_load_state("networkidle", timeout=60000)
        record("a token from before logout still works (no 403)", "/chat" in page.url, page.url)

        ctx.close()
        b.close()

    passed = sum(1 for _, ok in results if ok)
    print()
    print("SCORE " + str(passed) + "/" + str(len(results)))
    print("console events: " + str(len(console)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
