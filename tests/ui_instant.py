import os
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "documents", "_extract", "ui_instant")
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8010"
EMAIL = "instant-" + str(int(time.time())) + "@example.com"
PASSWORD = "instant-password-1"

results = []


def shot(page, name):
    path = os.path.join(OUT, name)
    page.screenshot(path=path, full_page=True)
    print("SHOT " + name + " " + str(os.path.getsize(path)))


def record(name, ok, detail=""):
    results.append((name, ok))
    print(("PASS " if ok else "FAIL ") + name + ("  " + detail if detail else ""))


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
            record_video_dir=OUT,
            record_video_size={"width": 390, "height": 844},
        )
        page = ctx.new_page()
        page.set_default_timeout(180000)
        page.goto(BASE + "/register", wait_until="networkidle")
        page.fill('input[name="name"]', "即時 太郎")
        page.fill('input[name="email"]', EMAIL)
        page.fill('input[name="password"]', PASSWORD)
        page.fill('input[name="password_confirm"]', PASSWORD)
        page.click('.form button[type="submit"]')
        page.wait_for_url("**/chat", timeout=60000)
        page.wait_for_timeout(400)

        record("chat page has the async form", page.locator('#chat-form[data-busy="0"]').count() == 1)

        page.fill('input[name="message"]', "今日 ランチ 850円")
        started = time.time()
        page.press('input[name="message"]', "Enter")

        page.wait_for_timeout(350)
        mid = time.time()
        bubble = page.locator("#thread .msg.me").last
        bubble_text = bubble.inner_text() if page.locator("#thread .msg.me").count() else ""
        dots = page.locator("#thread .thinking").count()
        input_value = page.input_value('input[name="message"]')
        shot(page, "01_instant.png")
        record(
            "user bubble appears before the reply",
            "850" in bubble_text,
            "at " + str(round((mid - started) * 1000)) + "ms the bubble reads: " + bubble_text.replace("\n", " "),
        )
        record("a thinking indicator is visible while waiting", dots == 1, "thinking nodes=" + str(dots))
        record("input clears immediately", input_value == "", "input=" + repr(input_value))

        page.wait_for_function(
            "() => document.getElementById('chat-form').dataset.busy === '0' "
            "&& document.querySelectorAll('#thread .thinking').length === 0 "
            "&& document.querySelectorAll('#thread .bot.entry').length > 0",
            timeout=180000,
        )
        done = time.time()
        shot(page, "02_reply.png")
        record("reply card arrives", "記録しました" in page.content(), "reply after " + str(round((done - started) * 1000)) + "ms")
        record("input is usable again", page.locator('#send-btn').is_enabled())

        page.fill('input[name="message"]', "今月の食費いくら?")
        page.press('input[name="message"]', "Enter")
        page.wait_for_function(
            "() => document.querySelectorAll('#thread .bot.answer').length > 0", timeout=180000
        )
        shot(page, "03_answer.png")
        record("second turn works without a page reload", "合計" in page.content())
        record("no full page navigation happened", page.evaluate("() => window.__navCount === undefined"))

        ctx.close()
        browser.close()

    passed = sum(1 for _, ok in results if ok)
    print()
    print("SCORE " + str(passed) + "/" + str(len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
