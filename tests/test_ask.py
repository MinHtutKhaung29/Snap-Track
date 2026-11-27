import json
import os
import sys
import time
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))

from app.chat import routes as chat_routes
from app.chat import service
from app.chat import tools
from app.main import app
from app.shared import ai, db

passed = 0
failed = []


def check(label, ok, detail=""):
    global passed
    passed += 1 if ok else 0
    print(("PASS " if ok else "FAIL ") + label + ("  " + detail if detail else ""))
    if not ok:
        failed.append(label + "  " + detail)


def rejects(args):
    try:
        tools.validate("ask_user", args)
    except tools.ToolError:
        return True
    except Exception:
        return False
    return False


GOOD = {"question": "コーヒーは300円ですか？", "yes": "300円", "no": "ちがう"}

decls = {decl["name"]: decl for decl in tools.TOOL_DECLS}
check("ask_user is declared", "ask_user" in decls)
decl = decls.get("ask_user") or {"parameters": {"properties": {}, "required": []}}
params = decl["parameters"]["properties"]
check("ask_user takes question, yes, no", sorted(params) == ["no", "question", "yes"], "got=" + str(sorted(params)))
check(
    "ask_user params are strings",
    all(params.get(key, {}).get("type") == "string" for key in ("question", "yes", "no")),
    "got=" + str(params),
)
check(
    "question, yes, no are required",
    sorted(decl["parameters"]["required"]) == ["no", "question", "yes"],
    "got=" + str(decl["parameters"]["required"]),
)
check("ask_user is not an execution tool", "ask_user" not in tools.COMMITMENT_TOOLS)

good = tools.validate("ask_user", GOOD)
check(
    "validate returns question, yes, no",
    sorted(good) == ["no", "question", "yes"],
    "got=" + str(sorted(good)),
)
check("validate keeps the question", good.get("question") == GOOD["question"], "got=" + str(good.get("question")))
check("validate keeps yes and no", (good.get("yes"), good.get("no")) == ("300円", "ちがう"), "got=" + str(good))
trimmed = tools.validate("ask_user", {"question": "  コーヒーは300円ですか？  ", "yes": " 300円 ", "no": " ちがう "})
check(
    "validate trims whitespace",
    trimmed == GOOD,
    "got=" + str(trimmed),
)
check("validate accepts a 200 char question", not rejects({**GOOD, "question": "あ" * 200}))
check("validate accepts 40 char labels", not rejects({**GOOD, "yes": "y" * 40, "no": "n" * 40}))

check("validate rejects an empty question", rejects({**GOOD, "question": "   "}))
check("validate rejects an empty yes", rejects({**GOOD, "yes": ""}))
check("validate rejects an empty no", rejects({**GOOD, "no": "  "}))
check("validate rejects a missing question", rejects({"yes": "300円", "no": "ちがう"}))
check("validate rejects a 201 char question", rejects({**GOOD, "question": "あ" * 201}))
check("validate rejects 41 char labels", rejects({**GOOD, "yes": "y" * 41}))
check("validate rejects a 41 char no", rejects({**GOOD, "no": "n" * 41}))
check("validate rejects a non-string question", rejects({**GOOD, "question": 300}))


def make_user():
    email = "ask-test-" + str(int(time.time() * 1000)) + "@example.invalid"
    return db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
        ("ask test", email, "x"),
    )


REPLIES = []


def fake_generate(system, contents, tool_defs=None, timeout=60):
    return REPLIES.pop(0) if REPLIES else {"text": "了解です。", "calls": []}


def card_payload(message_id):
    row = db.fetch_one("SELECT payload FROM chat_message WHERE message_id = %s", (message_id,))
    if not row or not row["payload"]:
        return None
    return json.loads(row["payload"]) if isinstance(row["payload"], str) else row["payload"]


user_id = make_user()
try:
    original = ai.generate
    ai.generate = fake_generate
    REPLIES.append({"text": None, "calls": [{"name": "ask_user", "args": dict(GOOD)}]})
    try:
        result = service.handle_turn(user_id, "コーヒー飲んだ")
    finally:
        ai.generate = original
    check("ask turn reports a question", result == {"ok": True, "type": "question"}, "got=" + str(result))

    rows = db.fetch_all(
        "SELECT message_id, role, body, payload FROM chat_message WHERE user_id = %s ORDER BY message_id",
        (user_id,),
    )
    cards = [row for row in rows if row["role"] == "assistant"]
    check("ask turn stores one assistant message", len(cards) == 1, "count=" + str(len(cards)))
    card = cards[0] if cards else {"body": None, "payload": None}
    payload = card["payload"]
    if isinstance(payload, str):
        payload = json.loads(payload)
    check("card body is the question", card["body"] == GOOD["question"], "got=" + str(card["body"]))
    check("card payload type is question", (payload or {}).get("type") == "question", "got=" + str(payload))
    check(
        "card payload keeps the question",
        (payload or {}).get("question") == GOOD["question"],
        "got=" + str((payload or {}).get("question")),
    )
    check(
        "card payload keeps the labels",
        ((payload or {}).get("yes"), (payload or {}).get("no")) == ("300円", "ちがう"),
        "got=" + str(payload),
    )
    check("card payload starts unanswered", "answer" in (payload or {}) and payload["answer"] is None, "got=" + str(payload))
    check(
        "card payload has exactly the agreed keys",
        sorted(payload or {}) == ["answer", "no", "question", "type", "yes"],
        "got=" + str(sorted(payload or {})),
    )

    card_id = card.get("message_id")
    original_generate = ai.generate
    original_user = chat_routes.auth.current_user
    original_token = chat_routes.csrf.verify_token
    ai.generate = fake_generate
    chat_routes.auth.current_user = lambda request: {"user_id": user_id}
    chat_routes.csrf.verify_token = lambda request, token: None
    try:
        REPLIES.append({"text": "記録しました。", "calls": []})
        response = chat_routes.chat_answer(SimpleNamespace(app=app), card_id, choice="yes", csrf_token="test")
        answered = json.loads(response.body)
        check("answer endpoint accepts a yes", response.status_code == 200, "got=" + str(response.status_code))
        check(
            "answer endpoint returns ok, html, card_html",
            sorted(answered) == ["card_html", "html", "ok"] and answered.get("ok") is True,
            "got=" + str(sorted(answered)),
        )
        check(
            "answer endpoint renders the card",
            bool(answered.get("card_html")),
            "got=" + str(answered.get("card_html"))[:60],
        )
        check(
            "answer endpoint renders new rows",
            bool(answered.get("html")),
            "got=" + str(answered.get("html"))[:60],
        )
        after = card_payload(card_id) or {}
        check("card payload stores the answer", after.get("answer") == "yes", "got=" + str(after.get("answer")))
        check(
            "card body stays the question",
            after.get("question") == GOOD["question"],
            "got=" + str(after.get("question")),
        )
        turns = db.fetch_all(
            "SELECT role, body FROM chat_message WHERE user_id = %s AND message_id > %s ORDER BY message_id",
            (user_id, card_id),
        )
        check(
            "yes label is sent as the user turn",
            bool(turns) and turns[0]["role"] == "user" and turns[0]["body"] == GOOD["yes"],
            "got=" + str(turns[:1]),
        )

        again = chat_routes.chat_answer(SimpleNamespace(app=app), card_id, choice="no", csrf_token="test")
        again_body = json.loads(again.body)
        check("second answer is refused", again.status_code == 409, "got=" + str(again.status_code))
        check("second answer reports answered", again_body.get("error") == "answered", "got=" + str(again_body))
        check("second answer keeps the first answer", (card_payload(card_id) or {}).get("answer") == "yes")

        plain = db.fetch_one(
            "SELECT message_id FROM chat_message WHERE user_id = %s AND role = 'user' ORDER BY message_id LIMIT 1",
            (user_id,),
        )
        foreign = chat_routes.chat_answer(SimpleNamespace(app=app), plain["message_id"], choice="yes", csrf_token="test")
        check("non-question row is refused", foreign.status_code == 409, "got=" + str(foreign.status_code))
    finally:
        ai.generate = original_generate
        chat_routes.auth.current_user = original_user
        chat_routes.csrf.verify_token = original_token
finally:
    db.execute("DELETE FROM ai_usage WHERE user_id = %s", (user_id,))
    db.execute("DELETE FROM chat_message WHERE user_id = %s", (user_id,))
    db.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
    left = db.fetch_one("SELECT COUNT(*) AS n FROM users WHERE user_id = %s", (user_id,))
    print("cleanup: users left=" + str(int(left["n"])))

total = passed + len(failed)
print()
print("SCORE " + str(passed) + "/" + str(total))
sys.exit(0 if not failed else 1)
