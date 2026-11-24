import re
import unicodedata
from datetime import date, datetime, timedelta, timezone

from app.shared import db
from app.shared.format import jp_date

JST = timezone(timedelta(hours=9))
MAX_AMOUNT = 10_000_000

TOOL_DECLS = [
    {
        "name": "record_expense",
        "description": "Record money the user spent, using an amount the user already stated.",
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {"type": "integer", "description": "whole yen, positive"},
                "date": {"type": "string", "description": "YYYY-MM-DD"},
                "source": {"type": "string", "description": "the shop, the item, or what the user called it (e.g. ランチ, コンビニ); empty only if the user gave nothing"},
                "category_code": {"type": "string", "enum": ["food", "transport", "daily", "social", "utility", "other"]},
                "memo": {"type": "string"},
            },
            "required": ["amount", "date", "category_code"],
        },
    },
    {
        "name": "record_income",
        "description": "Record money the user received.",
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {"type": "integer"},
                "date": {"type": "string", "description": "YYYY-MM-DD"},
                "source": {"type": "string"},
                "category_code": {"type": "string", "enum": ["salary", "support", "other_income"]},
            },
            "required": ["amount", "date", "category_code"],
        },
    },
    {
        "name": "query_money",
        "description": "Read the user's recorded money. Use for any question about totals or spending.",
        "parameters": {
            "type": "object",
            "properties": {
                "from": {"type": "string", "description": "YYYY-MM-DD"},
                "to": {"type": "string", "description": "YYYY-MM-DD"},
                "kind": {"type": "string", "enum": ["expense", "income"]},
                "category_code": {"type": "string"},
            },
            "required": ["from", "to", "kind"],
        },
    },
]

CATEGORY_LABEL = {}


class ToolError(Exception):
    pass


def today_jst():
    return datetime.now(JST).date()


def normalize(text):
    return unicodedata.normalize("NFKC", text or "")


def digits_in(text):
    cleaned = normalize(text).replace(",", "").replace("，", "")
    return set(re.findall(r"\d+", cleaned))


EXPLICIT_DATE = re.compile(
    r"(\d{4}-\d{1,2}-\d{1,2})|(\d{1,2}月\d{1,2}日)|(\b\d{1,2}/\d{1,2}\b)|(今日|きょう|昨日|きのう|おととい)"
)


def has_explicit_date(text):
    return EXPLICIT_DATE.search(normalize(text)) is not None


def load_categories():
    rows = db.fetch_all("SELECT category_id, code, kind, category_name FROM categories")
    mapping = {}
    for row in rows:
        mapping[(row["kind"], row["code"])] = row
        CATEGORY_LABEL[(row["kind"], row["code"])] = row["category_name"]
    return mapping


def category_for(kind, code):
    rows = db.fetch_all(
        "SELECT category_id, category_name FROM categories WHERE kind = %s AND code = %s",
        (kind, code),
    )
    if not rows:
        raise ToolError("unknown category " + str(code) + " for " + kind)
    return rows[0]


def parse_date(value):
    try:
        parsed = datetime.strptime(str(value), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ToolError("date must be YYYY-MM-DD")
    if parsed > today_jst():
        raise ToolError("date is in the future")
    if parsed.year < 2000:
        raise ToolError("date is implausible")
    return parsed


def parse_amount(value):
    try:
        amount = int(value)
    except (TypeError, ValueError):
        raise ToolError("amount must be an integer")
    if amount <= 0:
        raise ToolError("amount must be positive")
    if amount > MAX_AMOUNT:
        raise ToolError("amount is implausibly large")
    return amount


def clean_text(value, limit):
    if value is None:
        return None
    text = str(value).strip()
    return text[:limit] if text else None


def validate(name, args):
    if name in ("record_expense", "record_income"):
        kind = "expense" if name == "record_expense" else "income"
        normalized = {
            "kind": kind,
            "amount": parse_amount(args.get("amount")),
            "txn_date": parse_date(args.get("date")),
            "source": clean_text(args.get("source"), 120),
            "memo": clean_text(args.get("memo"), 255),
        }
        normalized["category"] = category_for(kind, args.get("category_code"))
        return normalized
    if name == "query_money":
        start = datetime.strptime(str(args.get("from")), "%Y-%m-%d").date()
        end = datetime.strptime(str(args.get("to")), "%Y-%m-%d").date()
        if end < start:
            raise ToolError("range is backwards")
        kind = args.get("kind")
        if kind not in ("expense", "income"):
            raise ToolError("kind must be expense or income")
        return {"from": start, "to": end, "kind": kind, "category_code": args.get("category_code")}
    raise ToolError("unknown tool " + str(name))


def execute(name, args, user_id):
    if name in ("record_expense", "record_income"):
        txn_id = db.execute(
            "INSERT INTO transactions (user_id, kind, amount, txn_date, category_id, source, memo, source_kind) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, 'chat')",
            (
                user_id,
                args["kind"],
                args["amount"],
                args["txn_date"],
                args["category"]["category_id"],
                args["source"],
                args["memo"],
            ),
        )
        return {
            "txn_id": txn_id,
            "kind": args["kind"],
            "amount": args["amount"],
            "date": args["txn_date"].isoformat(),
            "date_label": jp_date(args["txn_date"]),
            "source": args["source"],
            "category": args["category"]["category_name"],
        }
    if name == "query_money":
        sql = (
            "SELECT c.category_name AS category, SUM(t.amount) AS total, COUNT(*) AS n "
            "FROM transactions t JOIN categories c ON c.category_id = t.category_id "
            "WHERE t.user_id = %s AND t.deleted_at IS NULL AND t.kind = %s "
            "AND t.txn_date BETWEEN %s AND %s "
        )
        params = [user_id, args["kind"], args["from"], args["to"]]
        if args.get("category_code"):
            sql += "AND c.code = %s "
            params.append(args["category_code"])
        sql += "GROUP BY c.category_id, c.category_name ORDER BY total DESC"
        rows = db.fetch_all(sql, tuple(params))
        total = sum(int(r["total"]) for r in rows)
        return {
            "kind": args["kind"],
            "from": args["from"].isoformat(),
            "to": args["to"].isoformat(),
            "total": total,
            "rows": [{"category": r["category"], "total": int(r["total"]), "count": int(r["n"])} for r in rows],
        }
    raise ToolError("unknown tool " + str(name))


def needs_confirmation(name, args, user_text):
    if name == "query_money":
        return None
    if str(args.get("amount")) not in digits_in(user_text):
        return "amount_not_in_message"
    if not has_explicit_date(user_text):
        return "date_inferred"
    return None
