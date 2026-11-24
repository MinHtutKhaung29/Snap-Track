import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))

from app.shared import db


def main():
    rows = db.fetch_all(
        "SELECT user_id, email, password_hash, created_at FROM users ORDER BY user_id"
    )
    print("users: " + str(len(rows)))
    problems = []
    for row in rows:
        h = row["password_hash"] or ""
        algo = h.split("$")[0] if "$" in h else "PLAINTEXT?"
        print("  #{} {} {} len={} at={}".format(row["user_id"], row["email"], algo, len(h), row["created_at"]))
        if not h.startswith("scrypt$"):
            problems.append(row["email"])
    print()
    print("all hashed with scrypt: " + str(not problems))
    if problems:
        print("plaintext or unknown: " + ", ".join(problems))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
