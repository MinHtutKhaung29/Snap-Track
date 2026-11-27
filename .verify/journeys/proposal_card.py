import _common as v

SAME_LINE = (
    "(() => { const items = Array.from(document.querySelectorAll('.msg.swipe .line > *'));"
    " if (items.length === 0) return {count: 0, rows: 0};"
    " const rects = items.map((n) => n.getBoundingClientRect());"
    " let rows = 0; let bottom = -1;"
    " rects.forEach((r) => { if (r.top >= bottom - 2) { rows += 1; bottom = r.bottom; } else { bottom = Math.max(bottom, r.bottom); } });"
    " return {count: items.length, rows: rows}; })()"
)

OVERFLOW = "document.documentElement.scrollWidth - document.documentElement.clientWidth"


def flow(page):
    address = v.email("card")
    v.register(page, address)
    uid = v.user_id(address)

    v.send(page, "先週の金曜 ランチ 1200円")
    page.wait_for_selector(".msg.swipe", timeout=150000)
    page.wait_for_timeout(500)
    card = page.locator(".msg.swipe").last
    v.record("a past date shows the confirm card", card.count() == 1, card.count())
    v.record("the card floats over the chat", page.locator(".modal-wrap .msg.swipe").count() == 1, page.locator(".modal-wrap .msg.swipe").count())
    v.record("the chat behind it is veiled", page.locator(".veil").count() == 1)
    v.record("the card is announced as a dialog", card.get_attribute("aria-modal") == "true")
    v.shot(page, "01-past-card.png", full=False)
    geometry = page.evaluate(SAME_LINE)
    v.record("amount, category, source and date share one row", geometry.get("count") == 4 and geometry.get("rows") == 1, geometry)
    line_text = card.locator(".line").inner_text().replace("\n", " ").strip()
    v.record("the line carries amount, category, source and short date", "¥1,200" in line_text and "食費" in line_text and "ランチ" in line_text and "/" in line_text, line_text)
    v.record("the long date is gone", "2026年" not in line_text, line_text)
    v.record("one warning, one short sentence", card.locator(".warn").count() == 1 and card.locator(".warn").first.inner_text().strip() == "日付は推測です", card.locator(".warn").first.inner_text() if card.locator(".warn").count() else "none")
    v.record("no hint text on the card", card.locator(".swipe-hint").count() == 0, card.locator(".swipe-hint").count())
    v.record("no 直す editor on the card", card.locator(".edit").count() == 0 and "直す" not in card.inner_text())
    v.record("both swipe buttons are kept", card.locator(".swipe-btn").count() == 2)
    v.record("the card has no second meta row", card.locator(".meta").count() == 0, card.locator(".meta").count())
    v.record("nothing overflows sideways", page.evaluate(OVERFLOW) <= 0, page.evaluate(OVERFLOW))

    page.keyboard.press("Escape")
    page.wait_for_timeout(350)
    v.record("Escape returns the card to the chat without saving", page.locator(".modal-wrap").count() == 0 and len(v.db().fetch_all("SELECT txn_id FROM transactions WHERE user_id = %s", (uid,))) == 0)
    v.record("the dismissed card stays in the thread", page.locator("#thread .msg.swipe").count() == 1)
    page.locator("#thread .msg.swipe").click()
    page.wait_for_timeout(350)
    v.record("tapping the card reopens it", page.locator(".modal-wrap .msg.swipe").count() == 1)

    page.mouse.click(6, 760)
    page.wait_for_timeout(300)
    v.record("an outside tap can never save", len(v.db().fetch_all("SELECT txn_id FROM transactions WHERE user_id = %s", (uid,))) == 0)

    if page.locator(".modal-wrap").count() == 0:
        page.locator("#thread .msg.swipe").click()
        page.wait_for_timeout(300)
    card = page.locator(".msg.swipe").last
    card.locator(".swipe-right").click()
    page.wait_for_load_state("networkidle", timeout=60000)
    page.wait_for_timeout(500)
    rows = v.db().fetch_all("SELECT amount FROM transactions WHERE user_id = %s AND deleted_at IS NULL", (uid,))
    v.record("the floating card still saves", len(rows) == 1 and int(rows[0]["amount"]) == 1200, rows)
    v.record("the result carries its own footer", page.locator("#thread .entry .foot").count() == 1)
    v.shot(page, "02-past-saved.png", full=False)

    v.send(page, "今日 ランチ")
    body = page.content()
    asked = "金額" in body or "いくら" in body
    v.record("a message without an amount is asked back", asked, "question shown" if asked else "no question found")
    rows_left = v.db().fetch_all("SELECT txn_id FROM transactions WHERE user_id = %s AND deleted_at IS NULL", (uid,))
    v.record("an unanswered message writes nothing", len(rows_left) == 1, rows_left)
    v.shot(page, "03-no-amount.png")


if __name__ == "__main__":
    v.main(flow)
