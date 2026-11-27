import os
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8010"
HEADED = os.environ.get("HEADED") == "1"


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not HEADED)
        context = browser.new_context(viewport={"width": 390, "height": 740}, locale="ja-JP")
        page = context.new_page()
        email = "perf-" + str(int(time.time() * 1000)) + "@example.com"
        page.goto(BASE + "/register", wait_until="networkidle")
        page.fill('input[name="name"]', "性能 太郎")
        page.fill('input[name="email"]', email)
        page.fill('input[name="password"]', "perf-test-123")
        page.fill('input[name="password_confirm"]', "perf-test-123")
        page.click('.form button[type="submit"]')
        page.wait_for_url("**/chat", timeout=30000)

        frames = page.evaluate(
            "() => new Promise(done => { const t = []; const start = performance.now();"
            " const tick = now => { t.push(now); if (now - start < 2000) requestAnimationFrame(tick); else done(t); };"
            " requestAnimationFrame(tick); })"
        )
        gaps = [round(b - a, 1) for a, b in zip(frames, frames[1:])]
        gaps.sort()
        p95 = gaps[int(len(gaps) * 0.95)] if gaps else 0

        page.fill('[name="message"]', "ランチ 850円")
        started = time.time()
        page.click("#send-btn")
        page.wait_for_function("() => !document.querySelector('.thinking')", timeout=120000)
        waited = time.time() - started
        send = page.evaluate(
            "() => { const e = performance.getEntriesByType('resource').filter(r => r.name.includes('/chat/send'));"
            " return e.map(r => ({ms: Math.round(r.duration), bytes: r.transferSize})); }"
        )
        nodes = page.evaluate("() => document.querySelectorAll('*').length")
        print("headed=%s frames=%d p95_gap_ms=%s max_gap_ms=%s" % (HEADED, len(gaps), p95, gaps[-1] if gaps else 0))
        print("send_endpoint=%s wall_until_reply=%.1fs nodes=%d" % (send, waited, nodes))
        context.close()
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
