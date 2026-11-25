import json
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from app.shared import db
from app.shared.config import settings

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
JST = timezone(timedelta(hours=9))


class AIError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(code)
        self.code = code
        self.detail = detail


class _QuotaExceeded(Exception):
    pass


def reserve_quota(user_id):
    today = datetime.now(JST).date()
    try:
        with db.cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO ai_usage (user_id, usage_date, call_count) VALUES (%s, %s, 1) "
                "ON DUPLICATE KEY UPDATE call_count = call_count + 1",
                (user_id, today),
            )
            cur.execute(
                "SELECT call_count FROM ai_usage WHERE user_id = %s AND usage_date = %s",
                (user_id, today),
            )
            row = cur.fetchone()
            count = int(row["call_count"]) if row else 0
            if count > settings.ai_daily_cap:
                raise _QuotaExceeded()
    except _QuotaExceeded:
        return False
    return True


def generate_raw(system, contents, schema, timeout=120):
    if settings.ai_mode == "stub":
        return json.dumps(
            {
                "is_receipt": True,
                "date": None,
                "shop": "テスト店",
                "amount": 648,
                "category_code": "food",
            },
            ensure_ascii=False,
        )
    if not settings.gemini_api_key:
        raise AIError("no_key", "GEMINI_API_KEY is empty")
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
            "responseSchema": schema,
        },
    }
    return _post(body, timeout)["text"]


def _post(body, timeout):
    request = urllib.request.Request(
        ENDPOINT.format(model=settings.gemini_model) + "?key=" + urllib.parse.quote(settings.gemini_api_key, safe=""),
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    last = None
    for attempt, wait in enumerate((timeout, timeout * 2, timeout * 2), start=1):
        try:
            with urllib.request.urlopen(request, timeout=wait) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            if 500 <= exc.code < 600 and attempt < 3:
                last = AIError("http_" + str(exc.code), detail)
                continue
            raise AIError("http_" + str(exc.code), detail)
        except Exception as exc:
            last = AIError(type(exc).__name__, str(exc)[:300])
            if attempt < 3:
                continue
            raise last
    else:
        raise last or AIError("retries_exhausted")
    candidates = payload.get("candidates") or [{}]
    parts = (candidates[0].get("content") or {}).get("parts") or []
    calls = [part["functionCall"] for part in parts if "functionCall" in part]
    text = "".join(part.get("text", "") for part in parts if "text" in part)
    return {"calls": calls, "text": text.strip()}


def generate(system, contents, tools=None, timeout=60):
    if settings.ai_mode == "stub":
        return stub(contents, tools)
    if not settings.gemini_api_key:
        raise AIError("no_key", "GEMINI_API_KEY is empty")
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": contents,
        "generationConfig": {"temperature": 0},
    }
    if tools:
        body["tools"] = [{"functionDeclarations": tools}]
    return _post(body, timeout)


def user_turn(text):
    return {"role": "user", "parts": [{"text": text}]}


STUB_CATEGORY = [
    (("ランチ", "ごはん", "飯", "食", "コンビニ", "カフェ", "コーヒー", "弁当", "寿司", "カレー"), "food"),
    (("電車", "バス", "タクシー", "交通", "ガソリン", "駐車場"), "transport"),
    (("洗剤", "ティッシュ", "日用品", "ドラッグ"), "daily"),
    (("飲み会", "交際", "プレゼント"), "social"),
    (("電気", "ガス", "水道", "光熱"), "utility"),
]

STUB_INCOME = (("給料", "給与", "バイト", "仕送り", "収入"), "salary")


def stub(contents, tools):
    names = {tool["name"] for tool in (tools or [])}
    last = ""
    for entry in reversed(contents):
        if entry.get("role") == "user":
            last = "".join(part.get("text", "") for part in entry.get("parts", []))
            break
    text = unicodedata.normalize("NFKC", last).replace(",", "")
    today = datetime.now(JST).date()

    if "いくら" in text or "how much" in text.lower():
        start = today.replace(day=1)
        args = {"from": start.isoformat(), "to": today.isoformat(), "kind": "expense"}
        for words, code in STUB_CATEGORY:
            if any(word in text for word in words):
                args["category_code"] = code
                break
        return {"calls": [{"name": "query_money", "args": args}], "text": ""}

    numbers = re.findall(r"\d+", text)
    if not numbers:
        return {"calls": [], "text": "金額を教えてください。"}

    income = any(word in text for word in STUB_INCOME[0])
    amount = int(numbers[0])

    if "昨日" in text or "きのう" in text:
        txn_date = today - timedelta(days=1)
    elif "先週" in text:
        txn_date = today - timedelta(days=7)
    else:
        txn_date = today

    if income:
        return {"calls": [{"name": "record_income", "args": {"amount": amount, "date": txn_date.isoformat(), "category_code": "salary"}}], "text": ""}

    code = "other"
    for words, candidate in STUB_CATEGORY:
        if any(word in text for word in words):
            code = candidate
            break
    source = "コンビニ" if "コンビニ" in text else ("ランチ" if "ランチ" in text else "")
    return {
        "calls": [
            {
                "name": "record_expense",
                "args": {"amount": amount, "date": txn_date.isoformat(), "category_code": code, "source": source},
            }
        ],
        "text": "",
    }
