import os

import _common as v

FIXTURE = os.path.join(v.ROOT, "documents", "_extract", "fixtures", "not_payment.png")


def flow(page):
    address = v.email("item")
    v.register(page, address)
    uid = v.user_id(address)
    if not os.path.exists(FIXTURE):
        v.record("item photo fixture available", False, FIXTURE)
        return
    page.goto(v.BASE + "/chat", wait_until="networkidle")
    page.set_input_files('input[name="photo"]', FIXTURE)
    page.wait_for_url("**/receipts", timeout=180000)
    page.wait_for_load_state("networkidle", timeout=120000)
    page.wait_for_timeout(400)
    v.shot(page, "01-item-asks-price.png")
    title = page.locator(".ask-title")
    title_text = title.first.inner_text().strip() if title.count() else ""
    v.record("an item photo asks for the price", "いくらでしたか" in title_text, title_text)
    amount = page.locator('input[name="amount"]').first
    v.record("the amount field is empty, nothing invented", amount.input_value().strip() == "", amount.input_value())
    v.record("the amount field is required", amount.get_attribute("required") is not None)
    v.record("the photo stays attached", page.locator(".shot .thumb").count() == 1)
    v.record("the keypad ships hidden for no-JS users", "data-pad hidden" in page.request.get(page.url).text())
    v.record("the keypad appears once JavaScript runs", page.locator("[data-pad]").is_visible())
    v.record("the phone keyboard is suppressed when the pad runs", amount.get_attribute("inputmode") == "none", amount.get_attribute("inputmode"))
    for key in ("5", "8", "0", "0"):
        page.locator('[data-key="%s"]' % key).click()
    v.record("the keypad types the price", amount.input_value() == "5800", amount.input_value())
    page.locator('[data-key="del"]').click()
    v.record("the delete key removes one digit", amount.input_value() == "580", amount.input_value())
    page.locator('[data-key="00"]').click()
    v.record("the double-zero key appends two digits", amount.input_value() == "58000", amount.input_value())
    page.locator('[data-key="del"]').click()
    page.locator('[data-key="del"]').click()
    v.record("the amount is back to what he meant", amount.input_value() == "580", amount.input_value())
    page.locator('[data-key="0"]').click()
    v.record("the pad can finish the price", amount.input_value() == "5800", amount.input_value())
    page.locator(".row-shop > summary").click()
    page.locator('input[name="shop"]').fill("スニーカー")
    v.shot(page, "02-keypad-filled.png", full=False)
    page.locator(".pad-save").click()
    page.wait_for_load_state("networkidle", timeout=120000)
    page.wait_for_timeout(400)
    row = v.db().fetch_one(
        "SELECT txn_id, amount, source, source_kind, receipt_id, txn_date FROM transactions "
        "WHERE user_id = %s AND deleted_at IS NULL ORDER BY txn_id DESC LIMIT 1",
        (uid,),
    )
    v.record("the typed price becomes the record", row is not None and row["amount"] == 5800, row)
    v.record("the record points at the photo", row is not None and row["source_kind"] == "photo" and row["receipt_id"] is not None, row)
    v.record("the shop he typed is kept", row is not None and row["source"] == "スニーカー", row)
    page.goto(v.BASE + "/chat", wait_until="networkidle")
    page.wait_for_timeout(400)
    v.shot(page, "02-item-recorded.png")
    page.goto(v.BASE + "/receipts", wait_until="networkidle")
    page.wait_for_timeout(400)
    v.record("the queue is empty after saving", page.locator(".empty-title").count() == 1)


if __name__ == "__main__":
    v.main(flow)
