import re
import unicodedata
from calendar import monthrange
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
    {
        "name": "create_bill",
        "description": "Create a recurring bill schedule, not a transaction. Use the stated yen amount.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "amount": {"type": "integer"},
                "due_day": {"type": "integer"},
                "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                "category_code": {
                    "type": "string",
                    "enum": ["food", "transport", "daily", "social", "utility", "other"],
                },
            },
            "required": ["title", "amount", "due_day", "start_date", "category_code"],
        },
    },
    {
        "name": "create_installment",
        "description": "Create a monthly installment schedule, not a transaction. Use the stated total yen amount.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "total_amount": {"type": "integer"},
                "months": {"type": "integer"},
                "due_day": {"type": "integer"},
                "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                "category_code": {
                    "type": "string",
                    "enum": ["food", "transport", "daily", "social", "utility", "other"],
                },
            },
            "required": ["title", "total_amount", "months", "due_day", "start_date", "category_code"],
        },
    },
    {
        "name": "list_commitments",
        "description": "List the user's commitments. Omit status for active commitments. Use before resolving a payment.",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["active", "done", "canceled"]},
            },
            "required": [],
        },
    },
    {
        "name": "mark_paid",
        "description": "Request confirmation of one payment for a commitment returned by list_commitments. Never invent an ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "commitment_id": {"type": "integer"},
            },
            "required": ["commitment_id"],
        },
    },
]

CATEGORY_LABEL = {}

COMMITMENT_TOOLS = ("create_bill", "create_installment", "list_commitments", "mark_paid")
CREATION_TOOLS = ("create_bill", "create_installment")
EXPENSE_CODES = ("food", "transport", "daily", "social", "utility", "other")
COMMITMENT_STATUSES = ("active", "done", "canceled")
MONTHS_MIN = 1
MONTHS_MAX = 24
MAX_ID = 4294967295
ISO_DAY = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
DECL_BY_NAME = {decl["name"]: decl for decl in TOOL_DECLS}


class ToolError(Exception):
    pass


def today_jst():
    return datetime.now(JST).date()


def normalize(text):
    return unicodedata.normalize("NFKC", text or "")


def digits_in(text):
    cleaned = normalize(text).replace(",", "").replace("，", "")
    return set(re.findall(r"\d+", cleaned))


DATE_TOKENS = [
    r"\d{4}[-/]\d{1,2}[-/]\d{1,2}",
    r"\d{1,2}月\d{1,2}日",
    r"(?<!\d)\d{1,2}/\d{1,2}(?!\d)",
]

NON_MONEY_TAIL = re.compile(r"(?:%|％|個|本|枚|時|分|回|件|人|歳|年|か月|日|割|g|kg|ml|L)")

MONEY_TOKEN = re.compile(r"(¥|￥)?\s*(\d+)\s*(円)?")


def money_tokens(text):
    cleaned = normalize(text).replace(",", "").replace("，", "")
    for pattern in DATE_TOKENS:
        cleaned = re.sub(pattern, " ", cleaned)
    explicit = set()
    loose = set()
    for match in MONEY_TOKEN.finditer(cleaned):
        value = int(match.group(2))
        tail = cleaned[match.end() : match.end() + 2]
        if NON_MONEY_TAIL.match(tail):
            continue
        loose.add(value)
        if match.group(1) or match.group(3):
            explicit.add(value)
    return explicit, loose


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


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def add_months(value, months):
    year, index = divmod(value.year * 12 + value.month - 1 + int(months), 12)
    month = index + 1
    return date(year, month, min(value.day, monthrange(year, month)[1]))


def commitment_title(value):
    if not isinstance(value, str):
        raise ToolError("title must be a string of 1 to 120 characters")
    text = value.strip()
    if not 1 <= len(text) <= 120:
        raise ToolError("title must be a string of 1 to 120 characters")
    return text


def commitment_amount(value, field):
    if not is_int(value):
        raise ToolError(field + " must be an integer")
    if value < 1:
        raise ToolError(field + " must be positive")
    if value > MAX_AMOUNT:
        raise ToolError(field + " is implausibly large")
    return value


def commitment_due_day(value):
    if not is_int(value) or not 1 <= value <= 31:
        raise ToolError("due_day must be an integer from 1 to 31")
    return value


def commitment_months(value):
    if not is_int(value) or not MONTHS_MIN <= value <= MONTHS_MAX:
        raise ToolError("months must be an integer from 1 to 24")
    return value


def commitment_start(value):
    if not isinstance(value, str) or not ISO_DAY.fullmatch(value):
        raise ToolError("start_date must be YYYY-MM-DD")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ToolError("start_date must be YYYY-MM-DD")
    if parsed.year < 2000:
        raise ToolError("start_date is implausible")
    if parsed > add_months(today_jst(), 12):
        raise ToolError("start_date must be within 12 months of today")
    return parsed


def commitment_category(code):
    if code not in EXPENSE_CODES:
        raise ToolError("category_code must be a seeded expense category")
    rows = db.fetch_all(
        "SELECT category_id, category_name FROM categories WHERE kind = 'expense' AND code = %s",
        (code,),
    )
    if not rows:
        raise ToolError("category_code must be a seeded expense category")
    return {"category_id": rows[0]["category_id"], "category_name": rows[0]["category_name"], "code": code}


def check_arguments(name, args):
    if not isinstance(args, dict):
        raise ToolError("arguments must be an object")
    decl = DECL_BY_NAME[name]
    properties = decl["parameters"]["properties"]
    extra = sorted(key for key in args if key not in properties)
    if extra:
        raise ToolError("unexpected argument: " + str(extra[0]))
    for key in decl["parameters"]["required"]:
        if key not in args:
            raise ToolError("missing argument: " + key)


def validate_commitment_tool(name, args):
    check_arguments(name, args)
    if name == "create_bill":
        return {
            "kind": "bill",
            "title": commitment_title(args["title"]),
            "amount": commitment_amount(args["amount"], "amount"),
            "total_amount": None,
            "months": None,
            "due_day": commitment_due_day(args["due_day"]),
            "start_date": commitment_start(args["start_date"]),
            "category": commitment_category(args["category_code"]),
        }
    if name == "create_installment":
        title = commitment_title(args["title"])
        total = commitment_amount(args["total_amount"], "total_amount")
        months = commitment_months(args["months"])
        due_day = commitment_due_day(args["due_day"])
        start = commitment_start(args["start_date"])
        category = commitment_category(args["category_code"])
        if total < months:
            raise ToolError("total_amount must be at least months")
        return {
            "kind": "installment",
            "title": title,
            "amount": total // months,
            "total_amount": total,
            "months": months,
            "due_day": due_day,
            "start_date": start,
            "category": category,
        }
    if name == "list_commitments":
        status = args.get("status", "active")
        if status not in COMMITMENT_STATUSES:
            raise ToolError("status must be active, done, or canceled")
        return {"status": status}
    if name == "mark_paid":
        value = args["commitment_id"]
        if not is_int(value) or not 1 <= value <= MAX_ID:
            raise ToolError("commitment_id must be an integer from 1 to 4294967295")
        return {"commitment_id": value}
    raise ToolError("unknown tool " + str(name))


def validate(name, args):
    if name in COMMITMENT_TOOLS:
        return validate_commitment_tool(name, args)
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
    try:
        amount = int(args.get("amount"))
    except (TypeError, ValueError):
        return "amount_not_in_message"
    explicit, loose = money_tokens(user_text)
    allowed = explicit if explicit else loose
    if amount not in allowed:
        return "amount_not_in_message"
    if not has_explicit_date(user_text):
        return "date_inferred"
    return None
