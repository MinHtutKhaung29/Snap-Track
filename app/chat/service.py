import json
from datetime import date

from app.shared import ai, db
from app.shared.config import settings
from app.chat import tools as toolbox

HISTORY_LIMIT = 20

SYSTEM = (
    "あなたは個人のお金管理アプリ「Snap & Track」の中のアシスタントです。"
    "今日は {today} です。ユーザーは日本語・英語・混在で話します。"
    "金額は必ずツールで記録します。金額・日付・カテゴリを推測してはいけません。"
    "ユーザーが金額を言わない場合は、ツールを呼ばずに短い質問を返してください。"
    "カテゴリは次のコードだけを使います: expense=food,transport,daily,social,utility,other / income=salary,support,other_income。"
    "雑談やお金と関係ない質問には、お金の記録を手伝うことだけできると短く答えてください。"
    "返答は日本語で、1〜2文の短い文にしてください。"
)


def check_quota(user_id):
    rows = db.fetch_all(
        "SELECT call_count FROM ai_usage WHERE user_id = %s AND usage_date = %s",
        (user_id, date.today()),
    )
    used = int(rows[0]["call_count"]) if rows else 0
    if used >= settings.ai_daily_cap:
        return False
    return True


def bump_quota(user_id):
    db.execute(
        "INSERT INTO ai_usage (user_id, usage_date, call_count) VALUES (%s, %s, 1) "
        "ON DUPLICATE KEY UPDATE call_count = call_count + 1",
        (user_id, date.today()),
    )


def load_history(user_id):
    rows = db.fetch_all(
        "SELECT role, body FROM chat_message WHERE user_id = %s ORDER BY message_id DESC LIMIT %s",
        (user_id, HISTORY_LIMIT),
    )
    rows.reverse()
    contents = []
    for row in rows:
        role = "user" if row["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": row["body"]}]})
    return contents


def store(user_id, role, body, payload=None):
    message_id = db.execute(
        "INSERT INTO chat_message (user_id, role, body, payload) VALUES (%s, %s, %s, %s)",
        (user_id, role, body, json.dumps(payload, ensure_ascii=False) if payload else None),
    )
    return message_id


def thread(user_id):
    rows = db.fetch_all(
        "SELECT message_id, role, body, payload, created_at FROM chat_message WHERE user_id = %s ORDER BY message_id",
        (user_id,),
    )
    for row in rows:
        if isinstance(row["payload"], str):
            try:
                row["payload"] = json.loads(row["payload"])
            except ValueError:
                row["payload"] = None
    return rows


def handle_turn(user_id, text):
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "empty"}
    store(user_id, "user", text)

    if not check_quota(user_id):
        store(user_id, "assistant", "本日の利用回数の上限に達しました。", {"type": "error", "code": "quota"})
        return {"ok": False, "error": "quota"}

    contents = load_history(user_id)
    try:
        bump_quota(user_id)
        result = ai.generate(SYSTEM.format(today=toolbox.today_jst().isoformat()), contents, tool_defs())
    except ai.AIError as exc:
        store(user_id, "assistant", "AIに接続できませんでした。少し待ってからもう一度お試しください。", {"type": "error", "code": exc.code})
        return {"ok": False, "error": exc.code}

    if not result["calls"]:
        body = result["text"] or "うまく理解できませんでした。もう一度お試しください。"
        store(user_id, "assistant", body, {"type": "text"})
        return {"ok": True, "type": "text"}

    call = result["calls"][0]
    name = call.get("name")
    args = call.get("args") or {}

    try:
        normalized = toolbox.validate(name, args)
    except toolbox.ToolError as exc:
        store(user_id, "assistant", "うまく理解できませんでした。金額と日付をもう一度教えてください。", {"type": "error", "code": "invalid", "detail": str(exc)})
        return {"ok": False, "error": "invalid"}

    if name == "query_money":
        data = toolbox.execute("query_money", normalized, user_id)
        body = format_answer(data)
        store(user_id, "assistant", body, {"type": "answer", "data": data})
        return {"ok": True, "type": "answer"}

    reason = toolbox.needs_confirmation(name, normalized, text)
    if reason:
        preview = {
            "kind": normalized["kind"],
            "amount": normalized["amount"],
            "date": normalized["txn_date"].isoformat(),
            "source": normalized["source"],
            "category": normalized["category"]["category_name"],
            "date_label": toolbox.jp_date(normalized["txn_date"]),
            "reason": reason,
        }
        body = "この内容で記録しますか？"
        store(
            user_id,
            "assistant",
            body,
            {"type": "proposal", "tool": name, "raw_args": args, "preview": preview, "status": "pending"},
        )
        return {"ok": True, "type": "proposal"}

    saved = toolbox.execute(name, normalized, user_id)
    body = "記録しました: " + describe(saved)
    store(user_id, "assistant", body, {"type": "saved", "txn": saved})
    return {"ok": True, "type": "saved", "txn": saved}


def tool_defs():
    return toolbox.TOOL_DECLS


def describe(item):
    parts = [
        item.get("date_label") or item.get("date", ""),
        item.get("source") or "内容未入力",
        item.get("category", ""),
        "¥" + contract_amount(item.get("amount")),
    ]
    return "・".join(p for p in parts if p)


def contract_amount(value):
    try:
        return "{:,}".format(int(value))
    except (TypeError, ValueError):
        return str(value)


def format_answer(data):
    if not data["rows"]:
        return data["from"] + " 〜 " + data["to"] + " の記録はありません。"
    head = "支出" if data["kind"] == "expense" else "収入"
    lines = [head + " 合計 ¥" + str(data["total"]) + "（" + data["from"] + " 〜 " + data["to"] + "）"]
    for row in data["rows"][:5]:
        lines.append("・" + row["category"] + " ¥" + str(row["total"]) + "（" + str(row["count"]) + "件）")
    return "\n".join(lines)
