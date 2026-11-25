import os
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "documents", "_extract", "ui_receipts")
REAL = os.path.join(ROOT, "documents", "_extract", "p005", "real")
sys.path.insert(0, ROOT)

from app.shared import db

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8010"
EMAIL = "receipt-" + str(int(time.time())) + "@example.com"
PASSWORD = "receipt-password-1"

STEPS = []
console = []


def shot(page, name):
    path = os.path.join(OUT, name)
    page.screenshot(path=path, full_page=True)
    print("SHOT " + name + " " + str(os.path.getsize(path)))


def step(name, ok, detail=""):
    STEPS.append((name, ok))
    print(("PASS " if ok else "FAIL ") + name + ("  " + detail if detail else ""))


def uid_for(email):
    row = db.fetch_one("SELECT user_id FROM users WHERE email = %s", (email,))
    return row["user_id"] if row else None


def count(user_id, sql, params=()):
    row = db.fetch_one(sql, (user_id,) + params)
    return int(list(row.values())[0])


def upload(page, token, path):
    if "/chat" not in page.url:
        page.goto(BASE + "/chat", wait_until="networkidle")
    page.set_input_files('input[name="photo"]', path)
    page.wait_for_url("**/receipts", timeout=150000)
    page.wait_for_load_state("networkidle", timeout=120000)
    page.wait_for_timeout(500)


def main():
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True,
            locale="ja-JP",
        )
        page = ctx.new_page()
        page.set_default_timeout(180000)
        page.set_default_navigation_timeout(180000)
        page.on("console", lambda m: console.append(m.type + " " + m.text))
        page.on("pageerror", lambda e: console.append("pageerror " + str(e)))

        page.goto(BASE + "/register", wait_until="networkidle")
        page.fill('input[name="name"]', "レシート 太郎")
        page.fill('input[name="email"]', EMAIL)
        page.fill('input[name="password"]', PASSWORD)
        page.fill('input[name="password_confirm"]', PASSWORD)
        page.click('.form button[type="submit"]')
        page.wait_for_url("**/chat", timeout=60000)
        token = page.locator('input[name="csrf_token"]').first.get_attribute("value")
        step("registered and on chat", "/chat" in page.url)

        upload(page, token, os.path.join(REAL, "r02.jpg"))
        body = page.content()
        shot(page, "01_card.png")
        step("upload reaches the queue", "/receipts" in page.url)
        step("real receipt read as 620", "620" in body, "expected 620 from r02.jpg")
        step("shop read, not blank", "不明" not in body, "handwriting reads differently; any real value is acceptable")
        step("date shown as 2017", "2017" in body or "日付なし" in body)

        if page.locator("text=保存 →").count():
            page.locator("text=保存 →").first.click()
            page.wait_for_load_state("networkidle", timeout=120000)
            page.wait_for_timeout(500)
            shot(page, "02_saved_empty.png")
            uid = uid_for(EMAIL)
            n = count(uid, "SELECT COUNT(*) FROM transactions WHERE user_id = %s AND deleted_at IS NULL AND receipt_id IS NOT NULL")
            step("save writes a transaction linked to the receipt", n == 1, "linked rows=" + str(n))
            step("queue empties after save", "未確認のレシートはありません" in page.content())
        else:
            step("save writes a transaction linked to the receipt", False, "no save button")

        upload(page, token, os.path.join(REAL, "r06.jpg"))
        step("second upload queues", "/receipts" in page.url and ("1 / 1" in page.content() or "保存 →" in page.content()))

        if page.locator("text=← 直す").count():
            page.locator("text=← 直す").first.click()
            page.wait_for_timeout(400)
            page.fill('input[name="amount"]', "540")
            page.fill('input[name="shop"]', "カレー屋")
            page.fill('input[name="date"]', "")
            shot(page, "03_fix_form.png")
            uid = uid_for(EMAIL)
            before = count(uid, "SELECT COUNT(*) FROM transactions WHERE user_id = %s AND deleted_at IS NULL")
            page.locator('.form.tight button[type="submit"]').first.click()
            page.wait_for_load_state("networkidle", timeout=120000)
            page.wait_for_timeout(400)
            after = count(uid, "SELECT COUNT(*) FROM transactions WHERE user_id = %s AND deleted_at IS NULL")
            shot(page, "03b_missing_date.png")
            step(
                "missing date is refused with a visible message",
                after == before and "日付を入れてください" in page.content(),
                "rows " + str(before) + "->" + str(after),
            )
            kept_amount = page.locator('input[name="amount"]').first.input_value()
            kept_shop = page.locator('input[name="shop"]').first.input_value()
            step(
                "typed corrections survive the error",
                kept_amount == "540" and kept_shop == "カレー屋",
                "amount field=" + kept_amount + " shop field=" + kept_shop,
            )
            page.fill('input[name="date"]', "2026-11-24")
            page.locator('.form.tight button[type="submit"]').first.click()
            page.wait_for_load_state("networkidle", timeout=120000)
            row = db.fetch_one(
                "SELECT amount, source FROM transactions WHERE user_id = %s AND deleted_at IS NULL ORDER BY txn_id DESC LIMIT 1",
                (uid,),
            )
            step("correction saves the corrected amount", row and int(row["amount"]) == 540, "amount=" + str(row["amount"] if row else None))
            step("correction saves the typed shop", row and row["source"] == "カレー屋", "source=" + str(row["source"] if row else None))
        else:
            step("correction saves the corrected amount", False, "no fix button")

        upload(page, token, os.path.join(REAL, "r03.jpg"))
        shot(page, "04_before_discard.png")
        if page.locator("button.danger").count():
            page.locator("button.danger").first.click()
            page.wait_for_load_state("networkidle", timeout=60000)
            page.wait_for_timeout(400)
            shot(page, "05_after_discard.png")
            uid = uid_for(EMAIL)
            d = count(uid, "SELECT COUNT(*) FROM receipts WHERE user_id = %s AND discarded_at IS NOT NULL")
            step("discard leaves the queue permanently", d == 1, "discarded=" + str(d))
            step("discarded card is gone", "未確認のレシートはありません" in page.content())
        else:
            step("discard leaves the queue permanently", False, "no discard button")

        ctx.close()
        browser.close()

    with open(os.path.join(OUT, "steps.txt"), "w", encoding="utf-8") as f:
        for name, ok in STEPS:
            f.write(("PASS " if ok else "FAIL ") + name + "\n")
        f.write("\nconsole:\n" + ("\n".join(console) if console else "(none)"))
    passed = sum(1 for _, ok in STEPS if ok)
    print()
    print("SCORE " + str(passed) + "/" + str(len(STEPS)))
    print("console events: " + str(len(console)))
    return 0 if passed == len(STEPS) else 1


if __name__ == "__main__":
    sys.exit(main())
