import json
import re
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

from app.shared.config import settings

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
JST = timezone(timedelta(hours=9))


class AIError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(code)
        self.code = code
        self.detail = detail


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
    request = urllib.request.Request(
        ENDPOINT.format(model=settings.gemini_model),
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": settings.gemini_api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise AIError("http_" + str(exc.code), exc.read().decode("utf-8", "replace")[:300])
    except Exception as exc:
        raise AIError(type(exc).__name__, str(exc)[:300])
    candidates = payload.get("candidates") or [{}]
    content = candidates[0].get("content") or {}
    parts = content.get("parts") or []
    calls = [part["functionCall"] for part in parts if "functionCall" in part]
    text = "".join(part.get("text", "") for part in parts if "text" in part)
    return {"calls": calls, "text": text.strip()}


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
