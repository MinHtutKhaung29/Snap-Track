from calendar import monthrange
from datetime import date, datetime, timedelta, timezone

from app.shared import db
from app.shared.format import jp_date

JST = timezone(timedelta(hours=9))
MAX_AMOUNT = 10_000_000
MONTHS_MIN = 1
MONTHS_MAX = 24
BILL_PAYMENT_LIMIT = 255
STATUSES = ("active", "done", "canceled")


class CommitmentError(Exception):
    pass


def today_jst():
    return datetime.now(JST).date()


def month_period(value, offset):
    year, month_index = divmod(value.year * 12 + value.month - 1 + int(offset), 12)
    return year, month_index + 1


def due_date_for_period(year, month, due_day):
    return date(year, month, min(int(due_day), monthrange(year, month)[1]))


def first_due_date(start_date, due_day):
    due = due_date_for_period(start_date.year, start_date.month, due_day)
    if due >= start_date:
        return due
    year, month = month_period(start_date, 1)
    return due_date_for_period(year, month, due_day)


def due_for_count(start_date, due_day, count):
    base = first_due_date(start_date, due_day)
    year, month = month_period(base, count)
    return due_date_for_period(year, month, due_day)


def next_due_after(due_date, due_day):
    year, month = month_period(due_date, 1)
    return due_date_for_period(year, month, due_day)


def payment_amount(kind, amount, total_amount, months, paid_count):
    if kind == "installment":
        months = int(months)
        if int(paid_count) + 1 >= months:
            return int(total_amount) - int(amount) * (months - 1)
    return int(amount)


def check_schedule(row):
    kind = row["kind"]
    paid_count = int(row["paid_count"])
    if kind == "installment":
        months = row["months"]
        total = row["total_amount"]
        if months is None or total is None:
            raise CommitmentError("commitment schedule is invalid")
        months = int(months)
        total = int(total)
        if not MONTHS_MIN <= months <= MONTHS_MAX:
            raise CommitmentError("commitment schedule is invalid")
        if not 0 <= paid_count < months:
            raise CommitmentError("commitment schedule is invalid")
        if total < months or int(row["amount"]) != total // months:
            raise CommitmentError("commitment schedule is invalid")
        return
    if kind == "bill":
        if row["months"] is not None or row["total_amount"] is not None:
            raise CommitmentError("commitment schedule is invalid")
        if paid_count >= BILL_PAYMENT_LIMIT:
            raise CommitmentError("bill payment count limit reached")
        return
    raise CommitmentError("commitment schedule is invalid")


CREATE_SQL = (
    "INSERT INTO commitments "
    "(user_id, category_id, kind, title, amount, total_amount, months, paid_count, due_day, "
    "start_date, next_due_date, status) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, 0, %s, %s, %s, 'active')"
)

LIST_SQL = (
    "SELECT c.commitment_id AS id, c.title, c.kind, c.amount, c.total_amount, c.next_due_date, "
    "c.paid_count, c.months, c.status, cat.category_name "
    "FROM commitments AS c JOIN categories AS cat ON cat.category_id = c.category_id "
    "WHERE c.user_id = %s AND c.status = %s "
    "ORDER BY c.next_due_date, c.commitment_id"
)

LOCK_SQL = (
    "SELECT c.commitment_id, c.category_id, c.kind, c.title, c.amount, c.total_amount, c.months, "
    "c.paid_count, c.due_day, c.start_date, c.next_due_date, c.status, cat.category_name "
    "FROM commitments AS c JOIN categories AS cat ON cat.category_id = c.category_id "
    "WHERE c.user_id = %s AND c.commitment_id = %s FOR UPDATE OF c"
)

LATEST_SQL = (
    "SELECT txn_id FROM transactions WHERE user_id = %s AND commitment_id = %s "
    "ORDER BY txn_id DESC LIMIT 1 FOR UPDATE"
)

LIVE_LATEST_SQL = (
    "SELECT txn_id FROM transactions WHERE user_id = %s AND commitment_id = %s "
    "AND deleted_at IS NULL ORDER BY txn_id DESC LIMIT 1 FOR UPDATE"
)


def project(row):
    item = {
        "id": int(row["id"]),
        "title": row["title"],
        "kind": row["kind"],
        "amount": int(row["amount"]),
        "total_amount": int(row["total_amount"]) if row["total_amount"] is not None else None,
        "next_due_date": row["next_due_date"],
        "paid_count": int(row["paid_count"]),
        "months": int(row["months"]) if row["months"] is not None else None,
        "status": row["status"],
        "category_name": row.get("category_name"),
    }
    item["next_due_date_label"] = jp_date(item["next_due_date"])
    item["next_amount"] = payment_amount(
        item["kind"], item["amount"], item["total_amount"], item["months"], item["paid_count"]
    )
    item["remaining"] = item["months"] - item["paid_count"] if item["months"] is not None else None
    return item


def create_commitment(cur, user_id, spec):
    kind = spec["kind"]
    due_day = int(spec["due_day"])
    start_date = spec["start_date"]
    title = spec["title"]
    if kind == "installment":
        total_amount = int(spec["total_amount"])
        months = int(spec["months"])
        if not MONTHS_MIN <= months <= MONTHS_MAX:
            raise CommitmentError("commitment schedule is invalid")
        if total_amount < months:
            raise CommitmentError("total_amount must be at least months")
        amount = total_amount // months
        if amount < 1 or amount > MAX_AMOUNT:
            raise CommitmentError("commitment schedule is invalid")
    elif kind == "bill":
        amount = int(spec["amount"])
        if amount < 1 or amount > MAX_AMOUNT:
            raise CommitmentError("commitment schedule is invalid")
        total_amount = None
        months = None
    else:
        raise CommitmentError("commitment schedule is invalid")
    next_due = first_due_date(start_date, due_day)
    cur.execute(
        CREATE_SQL,
        (
            user_id,
            spec["category_id"],
            kind,
            title,
            amount,
            total_amount,
            months,
            due_day,
            start_date,
            next_due,
        ),
    )
    return {
        "id": int(cur.lastrowid),
        "kind": kind,
        "title": title,
        "amount": amount,
        "total_amount": total_amount,
        "months": months,
        "paid_count": 0,
        "due_day": due_day,
        "start_date": start_date,
        "next_due_date": next_due,
        "next_due_date_label": jp_date(next_due),
        "status": "active",
        "category_name": spec.get("category_name"),
    }


def list_commitments(user_id, status="active", limit=None):
    if status not in STATUSES:
        raise CommitmentError("status must be active, done, or canceled")
    sql = LIST_SQL
    params = [user_id, status]
    if limit:
        sql += " LIMIT %s"
        params.append(int(limit))
    return [project(row) for row in db.fetch_all(sql, tuple(params))]


def get_commitment(user_id, commitment_id):
    rows = db.fetch_all(
        "SELECT c.commitment_id AS id, c.title, c.kind, c.amount, c.total_amount, c.next_due_date, "
        "c.paid_count, c.months, c.status, cat.category_name "
        "FROM commitments AS c JOIN categories AS cat ON cat.category_id = c.category_id "
        "WHERE c.user_id = %s AND c.commitment_id = %s",
        (user_id, commitment_id),
    )
    return project(rows[0]) if rows else None


def latest_txn_id(user_id, commitment_id):
    row = db.fetch_one(LATEST_SQL.replace(" FOR UPDATE", ""), (user_id, commitment_id))
    return int(row["txn_id"]) if row else 0


def mark_paid(
    cur,
    user_id,
    commitment_id,
    expected_due_date=None,
    expected_last_txn_id=None,
    source_kind="manual",
    as_of=None,
):
    as_of = as_of or today_jst()
    cur.execute(LOCK_SQL, (user_id, commitment_id))
    row = cur.fetchone()
    if not row:
        raise CommitmentError("commitment not found")
    if row["status"] != "active":
        raise CommitmentError("commitment is not active")
    check_schedule(row)

    cur.execute(LATEST_SQL, (user_id, commitment_id))
    latest = cur.fetchone()
    current_last_txn_id = int(latest["txn_id"]) if latest else 0
    locked_due = row["next_due_date"]
    if expected_due_date is not None and expected_due_date != locked_due:
        raise CommitmentError("payment is stale")
    if expected_last_txn_id is not None and int(expected_last_txn_id) != current_last_txn_id:
        raise CommitmentError("payment is stale")
    if locked_due > as_of:
        raise CommitmentError("payment is not due yet")

    kind = row["kind"]
    paid_count = int(row["paid_count"])
    amount = payment_amount(kind, row["amount"], row["total_amount"], row["months"], paid_count)
    new_count = paid_count + 1
    done = kind == "installment" and new_count >= int(row["months"])
    new_status = "done" if done else "active"
    new_due = locked_due if done else next_due_after(locked_due, row["due_day"])

    cur.execute(
        "INSERT INTO transactions (user_id, kind, amount, txn_date, category_id, source, commitment_id, source_kind) "
        "VALUES (%s, 'expense', %s, %s, %s, %s, %s, %s)",
        (user_id, amount, as_of, row["category_id"], row["title"], row["commitment_id"], source_kind),
    )
    txn_id = int(cur.lastrowid)
    cur.execute(
        "UPDATE commitments SET paid_count = %s, next_due_date = %s, status = %s "
        "WHERE user_id = %s AND commitment_id = %s AND status = 'active'",
        (new_count, new_due, new_status, user_id, row["commitment_id"]),
    )
    if cur.rowcount != 1:
        raise CommitmentError("commitment update failed")
    return {
        "txn_id": txn_id,
        "kind": "expense",
        "amount": amount,
        "date": as_of.isoformat(),
        "date_label": jp_date(as_of),
        "source": row["title"],
        "category": row["category_name"],
        "commitment_id": int(row["commitment_id"]),
        "paid_count": new_count,
        "status": new_status,
        "next_due_date": new_due.isoformat(),
        "next_due_date_label": jp_date(new_due),
    }


def undo_payment(cur, user_id, txn_id):
    cur.execute(
        "SELECT txn_id, commitment_id FROM transactions WHERE txn_id = %s AND user_id = %s",
        (txn_id, user_id),
    )
    target = cur.fetchone()
    if not target or target["commitment_id"] is None:
        return None
    commitment_id = int(target["commitment_id"])

    cur.execute(LOCK_SQL, (user_id, commitment_id))
    row = cur.fetchone()
    if not row or row["status"] not in ("active", "done") or int(row["paid_count"]) < 1:
        raise CommitmentError("payment not found")

    cur.execute(LIVE_LATEST_SQL, (user_id, commitment_id))
    latest = cur.fetchone()
    if not latest or int(latest["txn_id"]) != int(txn_id):
        raise CommitmentError("only the latest payment can be undone")

    cur.execute(
        "UPDATE transactions SET deleted_at = NOW() WHERE user_id = %s AND commitment_id = %s "
        "AND txn_id = %s AND deleted_at IS NULL AND created_at >= NOW() - INTERVAL 24 HOUR",
        (user_id, commitment_id, txn_id),
    )
    if cur.rowcount != 1:
        raise CommitmentError("payment undo window expired")

    new_count = int(row["paid_count"]) - 1
    restored_due = due_for_count(row["start_date"], row["due_day"], new_count)
    cur.execute(
        "UPDATE commitments SET paid_count = %s, next_due_date = %s, status = 'active' "
        "WHERE user_id = %s AND commitment_id = %s",
        (new_count, restored_due, user_id, commitment_id),
    )
    if cur.rowcount != 1:
        raise CommitmentError("commitment update failed")
    return {
        "commitment_id": commitment_id,
        "paid_count": new_count,
        "status": "active",
        "next_due_date": restored_due,
        "next_due_date_label": jp_date(restored_due),
    }
