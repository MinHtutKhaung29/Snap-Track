import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.shared import db


def main():
    rows = db.fetch_all("SELECT user_id FROM users WHERE email LIKE 'verify-%@example.com'")
    for row in rows:
        db.execute("DELETE FROM transactions WHERE user_id = %s", (row["user_id"],))
        db.execute("DELETE FROM chat_message WHERE user_id = %s", (row["user_id"],))
        db.execute("UPDATE receipts SET discarded_at = NOW() WHERE user_id = %s", (row["user_id"],))
    print("cleaned scratch rows for " + str(len(rows)) + " throwaway verification users; evidence kept")
    return 0


if __name__ == "__main__":
    sys.exit(main())
