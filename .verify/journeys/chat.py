import _common as v


def flow(page):
    address = v.email("chat")
    v.register(page, address)
    uid = v.user_id(address)
    v.record("registered and reached chat", uid is not None, "user_id=" + str(uid))
    v.record(
        "greeting card is shown before the first message",
        page.locator(".intro .hello").count() == 1 and page.locator(".intro .chip").count() == 2,
    )

    bubble, to_bubble, to_reply = v.send(page, "今日 ランチ 850円")
    v.record("message bubble shows before the reply", "850" in bubble, str(to_bubble) + "ms")
    v.record(
        "greeting card leaves once a message exists",
        page.locator(".intro").count() == 0,
    )
    v.record("reply arrives", "記録しました" in page.content(), str(to_reply) + "ms")
    times = page.locator("#thread .pair .ts")
    v.record(
        "the appended card carries a time without a reload",
        times.count() > 0,
        times.first.inner_text() if times.count() else "no timestamp rendered",
    )
    rows = v.db().fetch_all(
        "SELECT amount, source_kind FROM transactions WHERE user_id = %s AND deleted_at IS NULL", (uid,)
    )
    v.record("exactly one expense row, from chat", len(rows) == 1 and int(rows[0]["amount"]) == 850, rows)
    v.shot(page, "01-chat-saved.png")

    before = len(rows)
    v.send(page, "先週の金曜 ランチ 1200円")
    after = v.db().fetch_all("SELECT txn_id FROM transactions WHERE user_id = %s AND deleted_at IS NULL", (uid,))
    v.record(
        "inferred date writes nothing until confirmed",
        len(after) == before,
        "rows " + str(before) + "->" + str(len(after)),
    )
    v.record("confirmation card is shown", "この内容で記録しますか" in page.content())
    v.shot(page, "02-chat-proposal.png")

    page.locator("text=保存する").first.click()
    page.wait_for_load_state("networkidle", timeout=60000)
    page.wait_for_timeout(400)
    confirmed = v.db().fetch_all(
        "SELECT amount FROM transactions WHERE user_id = %s AND deleted_at IS NULL", (uid,)
    )
    v.record("confirm writes the row", len(confirmed) == before + 1, "rows=" + str(len(confirmed)))

    page.locator("text=取り消す").first.click()
    page.wait_for_load_state("networkidle", timeout=60000)
    page.wait_for_timeout(400)
    live = v.db().fetch_all("SELECT txn_id FROM transactions WHERE user_id = %s AND deleted_at IS NULL", (uid,))
    v.record("undo soft-deletes", len(live) == len(confirmed) - 1, "live rows=" + str(len(live)))
    v.shot(page, "03-chat-undone.png")

    v.send(page, "今月の食費いくら？")
    v.record("query answers from SQL", "合計" in page.content())
    v.shot(page, "04-chat-answer.png")


if __name__ == "__main__":
    v.main(flow)
