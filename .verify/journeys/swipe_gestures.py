import _common as v

CARD = ".msg.swipe[data-state=open]"

READ_X = (
    "(() => {"
    " const card = document.querySelector('.msg.swipe');"
    " if (!card) return null;"
    " const m = new DOMMatrix(getComputedStyle(card).transform);"
    " return Math.round(m.m41);"
    "})()"
)

READ_ALL = (
    "(() => {"
    " const card = document.querySelector('.msg.swipe');"
    " if (!card) return null;"
    " const m = new DOMMatrix(getComputedStyle(card).transform);"
    " return {"
    "  x: Math.round(m.m41),"
    "  deg: Math.round(Math.atan2(m.m12, m.m11) * 180 / Math.PI * 10) / 10,"
    "  transition: getComputedStyle(card).transitionDuration"
    " };"
    "})()"
)


def rows(uid):
    return v.db().fetch_all(
        "SELECT txn_id, amount FROM transactions WHERE user_id = %s AND deleted_at IS NULL", (uid,)
    )


def new_card(page, text):
    v.send(page, text)
    page.wait_for_selector(CARD, timeout=150000)
    page.wait_for_timeout(400)
    return page.locator(CARD).bounding_box()


def grab(page, box, offset):
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + 40)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] / 2 + offset, box["y"] + 40, steps=4)
    page.wait_for_timeout(60)


def flow(page):
    address = v.email("swipe")
    v.register(page, address)
    uid = v.user_id(address)

    box = new_card(page, "先週の金曜 コーヒー 480円")
    grab(page, box, 140)
    pulled = page.evaluate(READ_ALL)
    v.record("a full pull follows the finger", bool(pulled) and pulled["x"] >= 120, pulled)
    v.record("a full pull tilts the card", bool(pulled) and abs(pulled["deg"]) >= 3, pulled and pulled["deg"])
    v.shot(page, "01-pulled-140.png")

    page.mouse.move(box["x"] + box["width"] / 2 + 60, box["y"] + 40, steps=3)
    page.wait_for_timeout(60)
    before_release = page.evaluate(READ_X)
    page.mouse.up()
    page.wait_for_timeout(70)
    during = page.evaluate(READ_X)
    page.wait_for_timeout(400)
    after = page.evaluate(READ_X)
    v.record(
        "an unfinished pull springs back instead of snapping",
        before_release is not None and during is not None and after is not None and abs(during - before_release) >= 3 and abs(after) <= 2,
        {"held_at": before_release, "70ms_after_release": during, "settled": after},
    )
    v.record("an unfinished pull records nothing", len(rows(uid)) == 0, rows(uid))
    v.record("the card is still open after an unfinished pull", page.locator(CARD).count() == 1)

    stamps = page.locator(CARD + " [data-stamp]").count()
    v.record("no idle hint text, drag stamps instead", stamps == 2 and page.locator(CARD + " [data-hint]").count() == 0, stamps)

    box = page.locator(CARD).bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + 40)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] / 2 + 34, box["y"] + 40, steps=1)
    page.mouse.up()
    page.wait_for_timeout(600)
    v.record(
        "a short flick is ignored",
        page.locator(CARD).count() == 1 and len(rows(uid)) == 0,
        {"cards": page.locator(CARD).count(), "transactions": len(rows(uid))},
    )

    box = page.locator(CARD).bounding_box()
    center_x = box["x"] + box["width"] / 2
    page.mouse.move(center_x, box["y"] + 40)
    page.mouse.down()
    page.mouse.move(center_x + 40, box["y"] + 180, steps=6)
    page.mouse.up()
    page.wait_for_timeout(500)
    v.record(
        "a mostly vertical drag scrolls instead of saving",
        page.locator(CARD).count() == 1 and len(rows(uid)) == 0,
        {"cards": page.locator(CARD).count(), "transactions": len(rows(uid))},
    )

    box = page.locator(CARD).bounding_box()
    grab(page, box, 130)
    page.mouse.up()
    page.wait_for_timeout(1400)
    v.record("a real swipe saves exactly one record", len(rows(uid)) == 1, rows(uid))
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(400)
    v.record(
        "the answer survives a reload",
        page.locator(CARD).count() == 0 and "記録しました" in page.content(),
        {"cards": page.locator(CARD).count()},
    )
    v.shot(page, "02-after-swipe-reload.png")

    new_card(page, "先週の金曜 パン 300円")
    page.locator(CARD).focus()
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(400)
    focused = page.evaluate("document.activeElement.className")
    v.record(
        "an arrow key moves focus instead of saving money",
        "swipe-right" in focused and len(rows(uid)) == 1,
        {"focused": focused, "transactions": len(rows(uid))},
    )
    page.keyboard.press("Enter")
    page.wait_for_timeout(1600)
    v.record("Enter on the focused choice commits it", len(rows(uid)) == 2, rows(uid))

    new_card(page, "先週の金曜 お茶 150円")
    page.emulate_media(reduced_motion="reduce")
    box = page.locator(CARD).bounding_box()
    grab(page, box, 130)
    page.mouse.up()
    page.wait_for_timeout(800)
    v.record("reduced motion still records the swipe", len(rows(uid)) == 3, rows(uid))
    page.emulate_media(reduced_motion="no-preference")


if __name__ == "__main__":
    v.main(flow)
