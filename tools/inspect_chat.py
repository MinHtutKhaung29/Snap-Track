import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))

from app.shared import db


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    rows = db.fetch_all(
        "SELECT m.message_id, m.user_id, m.role, m.body, m.payload FROM chat_message m "
        "ORDER BY m.message_id DESC LIMIT %s",
        (limit,),
    )
    rows.reverse()
    print("chat messages: " + str(len(rows)))
    for row in rows:
        payload = row["payload"]
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except ValueError:
                payload = {"raw": payload}
        kind = payload.get("type") if isinstance(payload, dict) else None
        extra = ""
        if isinstance(payload, dict):
            if kind == "error":
                extra = " code=" + str(payload.get("code")) + " detail=" + str(payload.get("detail"))[:120]
            elif kind == "saved":
                extra = " txn=" + str((payload.get("txn") or {}).get("txn_id"))
            elif kind == "proposal":
                extra = " status=" + str(payload.get("status"))
        body = (row["body"] or "").replace("\n", " / ")[:110]
        print("  #{} u{} {} [{}] {}{}".format(row["message_id"], row["user_id"], row["role"], kind, body, extra))
    usage = db.fetch_all("SELECT user_id, usage_date, call_count FROM ai_usage ORDER BY usage_date DESC LIMIT 5")
    print()
    print("ai_usage: " + str(usage))
    return 0


if __name__ == "__main__":
    sys.exit(main())
