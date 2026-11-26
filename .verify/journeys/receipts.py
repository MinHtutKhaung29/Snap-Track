import re

import _common as v

LONG_RECIPIENT = "株式会社エヌ・ティ・ティ・ドコモ・モバイル・コミュニケーションズ東日本支社お客様センター"


def flow(page):
    address = v.email("receipts")
    v.register(page, address)
    uid = v.user_id(address)
    image = v.receipt_photo()
    if not image:
        v.record("receipt photo fixture available", False, "no fixture under documents/_extract/p005/real")
        return
    page.goto(v.BASE + "/chat", wait_until="networkidle")
    page.set_input_files('input[name="photo"]', image)
    page.wait_for_url("**/receipts", timeout=180000)
    page.wait_for_load_state("networkidle", timeout=120000)
    page.wait_for_timeout(400)
    v.shot(page, "01-receipt-card.png")
    v.record("receipt card renders", page.locator(".row-hero").count() == 1)
    v.record("card offers one primary action", page.locator(".actions .primary").count() == 1)
    date_text = page.locator(".row", has_text="日付").first.locator(".row-v").inner_text().strip()
    v.record(
        "date reads in the Japanese long form",
        bool(re.fullmatch(r"\d{4}年\d{1,2}月\d{1,2}日（[月火水木金土日]）", date_text)),
        date_text,
    )
    shop = page.locator(".row-shop .row-v").first
    shop.evaluate("(el, s) => { el.textContent = s; }", LONG_RECIPIENT)
    page.wait_for_timeout(150)
    box = shop.evaluate(
        "(el) => ({client: el.clientWidth, scroll: el.scrollWidth,"
        " page: document.documentElement.scrollWidth - document.documentElement.clientWidth})"
    )
    v.record("long recipient wraps instead of clipping", box["scroll"] <= box["client"] + 1 and box["page"] <= 0, box)
    v.shot(page, "01b-long-recipient.png")
    page.goto(v.BASE + "/receipts", wait_until="networkidle")
    page.wait_for_timeout(400)
    page.locator(".actions .primary").first.click()
    page.wait_for_load_state("networkidle", timeout=120000)
    page.wait_for_timeout(400)
    row = v.db().fetch_one(
        "SELECT txn_id, amount, source_kind, receipt_id FROM transactions "
        "WHERE user_id = %s AND deleted_at IS NULL ORDER BY txn_id DESC LIMIT 1",
        (uid,),
    )
    v.record(
        "saved row is linked to the photo",
        row is not None and row["source_kind"] == "photo" and row["receipt_id"] is not None,
        row,
    )
    v.shot(page, "02-receipt-saved.png")


if __name__ == "__main__":
    v.main(flow)
