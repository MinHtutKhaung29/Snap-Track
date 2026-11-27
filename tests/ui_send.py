import os
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "documents", "_extract", "ui-send")
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8010"
HEADED = os.environ.get("HEADED") == "1"


def run(pw, label, width, height, scheme, mobile):
    browser = pw.chromium.launch(
        headless=not HEADED,
        slow_mo=400 if HEADED else 0,
        args=["--window-position=120,120"] if HEADED else None,
    )
    context = browser.new_context(
        viewport={"width": width, "height": height},
        device_scale_factor=2,
        is_mobile=mobile,
        has_touch=mobile,
        locale="ja-JP",
        color_scheme=scheme,
    )
    page = context.new_page()
    page.bring_to_front()
    email = "send-" + label + "-" + str(int(time.time() * 1000)) + "@example.com"
    page.goto(BASE + "/register", wait_until="networkidle")
    page.fill('input[name="name"]', "テスト 太郎")
    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', "ui-test-password-1")
    page.fill('input[name="password_confirm"]', "ui-test-password-1")
    page.click('.form button[type="submit"]')
    page.wait_for_url("**/chat", timeout=30000)
    page.wait_for_timeout(1200)
    page.screenshot(path=os.path.join(OUT, label + "_empty.png"))
    print("SHOT " + label + "_empty.png disabled=" + str(page.locator("#send-btn").is_disabled()))
    page.fill('[name="message"]', "今日 ランチ 850円")
    page.wait_for_timeout(250)
    box = page.locator("#send-btn").bounding_box()
    print("BOX " + label + " " + str(round(box["width"])) + "x" + str(round(box["height"])))
    page.screenshot(path=os.path.join(OUT, label + "_typed.png"))
    print("SHOT " + label + "_typed.png disabled=" + str(page.locator("#send-btn").is_disabled()))
    if label == "phone_light":
        page.wait_for_timeout(900)
        with page.expect_request("**/chat/send") as call:
            page.click("#send-btn")
        page.wait_for_selector("#thread .msg.me", timeout=5000)
        print("SUBMIT ok " + call.value.url + " bubble=" + str(page.locator("#thread .msg.me").count()))
        try:
            page.wait_for_selector("#thread .msg.bot", timeout=90000)
            print("REPLY ok bot=" + str(page.locator("#thread .msg.bot").count()))
        except Exception as exc:
            print("REPLY timeout " + type(exc).__name__)
        page.wait_for_timeout(6000 if HEADED else 900)
        page.screenshot(path=os.path.join(OUT, label + "_sent.png"))
        print("SHOT " + label + "_sent.png")
    if HEADED:
        page.bring_to_front()
        page.wait_for_timeout(int(os.environ.get("HOLD", "60")) * 1000)
    context.close()
    browser.close()


def main():
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    configs = [
        ("phone_light", 390, 844, "light", True),
        ("phone_dark", 390, 844, "dark", True),
        ("desktop_light", 1280, 800, "light", False),
        ("desktop_dark", 1280, 800, "dark", False),
    ]
    with sync_playwright() as pw:
        for config in configs:
            if only and config[0] not in only:
                continue
            run(pw, *config)
    print("output: " + OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
