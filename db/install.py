import os
import sys
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import schema

ROOT = HERE.parent
load_dotenv(ROOT / ".env")


def connect(as_root=True):
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("DB_PORT", "3306")),
        user="root" if as_root else os.environ["DB_USER"],
        password=os.environ["DB_ROOT_PASSWORD"] if as_root else os.environ["DB_PASSWORD"],
        database=os.environ.get("DB_NAME", "snapandtrack"),
        charset="utf8mb4",
        connection_timeout=10,
        autocommit=False,
    )


def main():
    conn = connect(as_root=True)
    cur = conn.cursor()
    cur.execute("SET time_zone = '+09:00'")

    present = schema.apply_schema(cur)
    counts = schema.seed_categories(cur)
    conn.commit()

    cur.execute("SHOW TABLES")
    tables = sorted(r[0] for r in cur.fetchall())
    cur.execute("SELECT kind, COUNT(*) FROM categories GROUP BY kind ORDER BY kind")
    cat_rows = cur.fetchall()
    cur.execute("SELECT category_name FROM categories WHERE kind='expense' ORDER BY sort_order")
    expense_names = [r[0] for r in cur.fetchall()]

    cur.close()
    conn.close()

    print("tables (" + str(len(tables)) + ")  " + ", ".join(tables))
    print("categories      " + ", ".join(f"{k}={v}" for k, v in cat_rows))
    print("expense names   " + ", ".join(expense_names))
    missing = [t for t in schema.ORDER if t not in tables]
    print("missing         " + (", ".join(missing) if missing else "none"))
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
