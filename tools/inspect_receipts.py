import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))

from app.shared import db


def main():
    rows = db.fetch_all(
        "SELECT receipt_id, user_id, image_path, read_status, discarded_at, extracted, uploaded_at "
        "FROM receipts ORDER BY receipt_id DESC LIMIT 8"
    )
    print("receipts: " + str(len(rows)))
    for r in rows:
        extracted = r["extracted"]
        if isinstance(extracted, str):
            extracted = extracted[:160]
        print(
            "  #{} u{} {} status={} discarded={} {}".format(
                r["receipt_id"], r["user_id"], r["image_path"], r["read_status"], bool(r["discarded_at"]), extracted
            )
        )
    linked = db.fetch_all(
        "SELECT txn_id, user_id, amount, source, receipt_id, source_kind FROM transactions "
        "WHERE receipt_id IS NOT NULL ORDER BY txn_id DESC LIMIT 5"
    )
    print()
    print("linked transactions: " + str(linked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
