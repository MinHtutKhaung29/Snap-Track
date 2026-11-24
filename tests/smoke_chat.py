import http.cookiejar
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))

from app.shared import db

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8010"
EMAIL = "chat-" + str(int(time.time())) + "@example.com"
PASSWORD = "chat-password-123"

results = []


def record(name, passed, detail=""):
    results.append((name, passed, detail))
    print(("PASS " if passed else "FAIL ") + name + ("  " + detail if detail else ""))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def opener():
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), NoRedirect)


def get(op, path):
    try:
        r = op.open(BASE + path, timeout=30)
        return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def post(op, path, data):
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        r = op.open(req, timeout=90)
        return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def csrf_of(html):
    m = re.search(r'name="csrf_token" value="([^"]+)"', html)
    return m.group(1) if m else None


def user_id_for(email):
    row = db.fetch_one("SELECT user_id FROM users WHERE email = %s", (email,))
    return row["user_id"] if row else None


def txn_count(uid):
    row = db.fetch_one(
        "SELECT COUNT(*) AS n FROM transactions WHERE user_id = %s AND deleted_at IS NULL", (uid,)
    )
    return int(row["n"])


def last_txn(uid):
    return db.fetch_one(
        "SELECT txn_id, amount, kind, source, txn_date FROM transactions WHERE user_id = %s "
        "ORDER BY txn_id DESC LIMIT 1",
        (uid,),
    )


def main():
    op = opener()
    status, html = get(op, "/register")
    token = csrf_of(html)
    status, html = post(
        op,
        "/register",
        {"name": "Chat Test", "email": EMAIL, "password": PASSWORD, "password_confirm": PASSWORD, "csrf_token": token},
    )
    record("register chat user", status == 303, "status=" + str(status))

    uid = user_id_for(EMAIL)
    record("user row created", uid is not None)

    status, html = get(op, "/chat")
    token = csrf_of(html)
    record("chat page renders", status == 200 and "thread" in html, "status=" + str(status))

    before = txn_count(uid)
    status, html = post(op, "/chat", {"message": "今日 ランチ 850円", "csrf_token": token})
    after = txn_count(uid)
    row = last_txn(uid)
    record("explicit amount saves without asking", status == 303 and after == before + 1 and row["amount"] == 850, "rows " + str(before) + "->" + str(after) + " amount=" + str(row["amount"] if row else None))

    _, html = get(op, "/chat")
    record("saved card shows undo", "元に戻す" in html)

    before = txn_count(uid)
    status, html = post(op, "/chat", {"message": "先週の金曜 ランチ 1200円", "csrf_token": token})
    _, page = get(op, "/chat")
    after = txn_count(uid)
    record(
        "inferred date asks before saving",
        after == before and "確認してください" in page and "保存する" in page,
        "rows " + str(before) + "->" + str(after),
    )

    m = re.search(r'action="/chat/confirm/(\d+)"', page)
    if m:
        status, html = post(op, "/chat/confirm/" + m.group(1), {"csrf_token": csrf_of(page)})
        after_confirm = txn_count(uid)
        record("confirm saves the row", after_confirm == before + 1, "rows=" + str(after_confirm))
    else:
        record("confirm saves the row", False, "no confirm button found")

    first = db.fetch_one(
        "SELECT txn_id FROM transactions WHERE user_id = %s AND amount = 850 ORDER BY txn_id LIMIT 1", (uid,)
    )
    if first:
        _, page = get(op, "/chat")
        status, html = post(op, "/undo/" + str(first["txn_id"]), {"csrf_token": csrf_of(page)})
        gone = db.fetch_one("SELECT deleted_at FROM transactions WHERE txn_id = %s", (first["txn_id"],))
        record("undo soft-deletes the row", status == 303 and gone["deleted_at"] is not None)
    else:
        record("undo soft-deletes the row", False, "850 row missing")

    status, html = post(op, "/chat", {"message": "今月の食費いくら?", "csrf_token": token})
    _, page = get(op, "/chat")
    tail = page.split("合計")[-1][:24]
    record(
        "query answers with the correct total",
        "合計" in page and "1200" in tail and "850" not in tail,
        "answer tail=" + tail.replace("\n", " ")[:40],
    )

    passed = sum(1 for _, p, _ in results if p)
    print()
    print("SCORE " + str(passed) + "/" + str(len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
