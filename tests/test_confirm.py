import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))

from app.chat import service
from app.chat import tools
from app.shared import db

REFUSAL = "24時間を過ぎた記録は取り消せません。"

passed = 0
failed = []


def check(label, ok, detail=""):
    global passed
    passed += 1 if ok else 0
    print(("PASS " if ok else "FAIL ") + label + ("  " + detail if detail else ""))
    if not ok:
        failed.append(label + "  " + detail)


def make_user():
    email = "confirm-test-" + str(int(time.time() * 1000)) + "@example.invalid"
    return db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
        ("confirm test", email, "x"),
    )


def make_proposal(user_id, amount, source):
    payload = {
        "type": "proposal",
        "tool": "record_expense",
        "raw_args": {
            "amount": amount,
            "date": tools.today_jst().isoformat(),
            "category_code": "food",
            "source": source,
        },
        "preview": {
            "kind": "expense",
            "amount": amount,
            "date": tools.today_jst().isoformat(),
            "source": source,
            "category": "食費",
            "date_label": tools.jp_date(tools.today_jst()),
            "reason": "date_inferred",
        },
        "status": "pending",
    }
    return db.execute(
        "INSERT INTO chat_message (user_id, role, body, payload) VALUES (%s, %s, %s, %s)",
        (user_id, "assistant", "この内容で記録しますか？", json.dumps(payload, ensure_ascii=False)),
    )


def make_txn(user_id, amount, source, created_at_sql, params_extra=()):
    category = tools.category_for("expense", "food")
    sql = (
        "INSERT INTO transactions (user_id, kind, amount, txn_date, category_id, source, source_kind, created_at) "
        "VALUES (%s, 'expense', %s, %s, %s, %s, 'chat', " + created_at_sql + ")"
    )
    params = (user_id, amount, tools.today_jst(), category["category_id"], source) + params_extra
    return db.execute(sql, params)


def count_txns(user_id):
    row = db.fetch_one("SELECT COUNT(*) AS n FROM transactions WHERE user_id = %s", (user_id,))
    return int(row["n"])


def txn_row(txn_id):
    return db.fetch_one("SELECT txn_id, deleted_at FROM transactions WHERE txn_id = %s", (txn_id,))


def message_payload(message_id):
    row = db.fetch_one("SELECT payload FROM chat_message WHERE message_id = %s", (message_id,))
    if not row or not row["payload"]:
        return None
    return json.loads(row["payload"]) if isinstance(row["payload"], str) else row["payload"]


def count_refusals(user_id):
    row = db.fetch_one(
        "SELECT COUNT(*) AS n FROM chat_message WHERE user_id = %s AND role = 'assistant' AND body = %s",
        (user_id, REFUSAL),
    )
    return int(row["n"])


user_id = make_user()
try:
    message_id = make_proposal(user_id, 850, "二重送信テスト")
    first = service.confirm(user_id, message_id, {"amount": "", "date": "", "category_code": ""})
    check("first confirm reports a save", bool(first), "got=" + str(first))
    after_first = count_txns(user_id)
    check("first confirm writes one transaction", after_first == 1, "count=" + str(after_first))

    second = service.confirm(user_id, message_id, {"amount": "", "date": "", "category_code": ""})
    check("second confirm reports no save", not second, "got=" + str(second))
    after_second = count_txns(user_id)
    check("second confirm writes nothing", after_second == 1, "count=" + str(after_second))

    saved_payload = message_payload(message_id) or {}
    check("proposal is marked saved", saved_payload.get("type") == "saved", "payload=" + str(saved_payload.get("type")))
    check(
        "saved payload keeps the txn id",
        bool((saved_payload.get("txn") or {}).get("txn_id")),
        "payload=" + str(saved_payload.get("txn")),
    )

    old_txn = make_txn(user_id, 1000, "古い記録", "NOW() - INTERVAL 25 HOUR")
    old_result = service.undo_transaction(user_id, old_txn)
    check("old undo is refused", old_result == "expired", "got=" + str(old_result))
    check("old row keeps deleted_at NULL", txn_row(old_txn)["deleted_at"] is None)
    check("old undo appends one refusal message", count_refusals(user_id) == 1, "count=" + str(count_refusals(user_id)))

    fresh_txn = make_txn(user_id, 1200, "新しい記録", "NOW()")
    fresh_result = service.undo_transaction(user_id, fresh_txn)
    check("fresh undo is applied", fresh_result == "undone", "got=" + str(fresh_result))
    check("fresh row gets deleted_at", txn_row(fresh_txn)["deleted_at"] is not None)
    check("fresh undo adds no refusal", count_refusals(user_id) == 1, "count=" + str(count_refusals(user_id)))

    again = service.undo_transaction(user_id, fresh_txn)
    check("second undo is ignored", again == "ignored", "got=" + str(again))
    check("second undo adds no refusal", count_refusals(user_id) == 1, "count=" + str(count_refusals(user_id)))

    other = service.undo_transaction(user_id + 100000, fresh_txn)
    check("foreign txn id is ignored", other == "ignored", "got=" + str(other))
finally:
    db.execute("DELETE FROM chat_message WHERE user_id = %s", (user_id,))
    db.execute("DELETE FROM transactions WHERE user_id = %s", (user_id,))
    db.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
    left = db.fetch_one("SELECT COUNT(*) AS n FROM users WHERE user_id = %s", (user_id,))
    print("cleanup: users left=" + str(int(left["n"])))

total = passed + len(failed)
print()
print("SCORE " + str(passed) + "/" + str(total))
sys.exit(0 if not failed else 1)
