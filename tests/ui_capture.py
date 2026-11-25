import os
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "documents", "_extract", "ui")
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8010"
EMAIL = "ui-" + str(int(time.time())) + "@example.com"
PASSWORD = "ui-test-password-1"

STEPS = []
console_log = []


def shot(page, name):
    path = os.path.join(OUT, name)
    page.screenshot(path=path, full_page=True)
    print("SHOT " + name + "  " + str(os.path.getsize(path)) + " bytes")
    return path


def step(name, ok, detail=""):
    STEPS.append((name, ok, detail))
    print(("PASS " if ok else "FAIL ") + name + ("  " + detail if detail else ""))


def send(page, text):
    before = page.locator("#thread .msg").count()
    page.fill('input[name="message"]', text)
    try:
        page.click('#send-btn', timeout=240000)
        page.wait_for_timeout(150)
        page.wait_for_function(
            "(n) => { var f = document.getElementById('chat-form'); return f.dataset.busy === '0' "
            "&& document.querySelectorAll('#thread .thinking').length === 0 "
            "&& document.querySelectorAll('#thread .msg').length > n; }",
            arg=before,
            timeout=240000,
        )
        page.wait_for_load_state("networkidle", timeout=60000)
    except Exception as exc:
        shot(page, "error_send_" + str(int(time.time())) + ".png")
        raise exc


def main():
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=2,
            is_mobile=True,
            has_touch=True,
            locale="ja-JP",
            record_video_dir=OUT,
            record_video_size={"width": 390, "height": 844},
        )
        page = context.new_page()
        page.set_default_timeout(240000)
        page.set_default_navigation_timeout(240000)
        page.on("console", lambda m: console_log.append("console:" + m.type + " " + m.text))
        page.on("pageerror", lambda e: console_log.append("pageerror: " + str(e)))
        page.on("requestfailed", lambda r: console_log.append("requestfailed: " + r.url + " " + str(r.failure)))

        page.goto(BASE + "/register", wait_until="networkidle")
        shot(page, "01_register.png")
        step("register page renders", page.locator('input[name="email"]').count() == 1)

        page.fill('input[name="name"]', "テスト 太郎")
        page.fill('input[name="email"]', EMAIL)
        page.fill('input[name="password"]', PASSWORD)
        page.fill('input[name="password_confirm"]', PASSWORD)
        page.click('.form button[type="submit"]')
        page.wait_for_url("**/chat", timeout=30000)
        page.wait_for_timeout(600)
        shot(page, "02_chat_empty.png")
        step("register lands on chat", "/chat" in page.url)

        send(page, "今日 ランチ 850円")
        page.wait_for_timeout(800)
        shot(page, "03_saved.png")
        step("explicit entry saves", "記録しました" in page.content())

        if page.locator("text=取り消す").count():
            page.locator("text=取り消す").first.click()
            page.wait_for_load_state("networkidle", timeout=60000)
            page.wait_for_timeout(600)
            shot(page, "04_undo.png")
            step("undo works", "取り消し済み" in page.content())
        else:
            step("undo works", False, "no undo button")

        send(page, "先週の金曜 ランチ 1200円")
        page.wait_for_timeout(800)
        shot(page, "05_proposal.png")
        step("inferred date asks first", "この内容で記録しますか" in page.content() and "保存する" in page.content())

        if page.locator("text=保存する").count():
            page.locator("text=保存する").first.click()
            page.wait_for_load_state("networkidle", timeout=60000)
            page.wait_for_timeout(600)
            shot(page, "06_confirmed.png")
            step("confirm writes the row", page.content().count("記録しました") >= 1)
        else:
            step("confirm writes the row", False, "no save button")

        send(page, "今月の食費いくら?")
        page.wait_for_timeout(800)
        shot(page, "07_answer.png")
        body = page.content()
        step("query answers", "合計" in body)

        send(page, "ランチ")
        page.wait_for_timeout(800)
        shot(page, "08_no_amount.png")
        step("missing amount does not invent one", "記録しました" not in page.content().split("ランチ")[-1])

        page.set_viewport_size({"width": 1280, "height": 900})
        page.wait_for_timeout(400)
        shot(page, "09_desktop.png")

        context.close()
        browser.close()

    with open(os.path.join(OUT, "console.log"), "w", encoding="utf-8") as f:
        f.write("\n".join(console_log) if console_log else "(no console output)")
    with open(os.path.join(OUT, "steps.txt"), "w", encoding="utf-8") as f:
        for name, ok, detail in STEPS:
            f.write(("PASS " if ok else "FAIL ") + name + " " + detail + "\n")

    passed = sum(1 for _, ok, _ in STEPS if ok)
    print()
    print("SCORE " + str(passed) + "/" + str(len(STEPS)))
    print("console events: " + str(len(console_log)))
    print("output: " + OUT)
    return 0 if passed == len(STEPS) else 1


if __name__ == "__main__":
    sys.exit(main())
