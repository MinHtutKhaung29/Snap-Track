import http.cookiejar
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8010"
EMAIL = "smoke-" + str(int(time.time())) + "@example.com"
PASSWORD = "smoke-password-123"

results = []


def record(name, passed, detail=""):
    results.append((name, passed, detail))
    print(("PASS " if passed else "FAIL ") + name + ("  " + detail if detail else ""))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def make_opener():
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), NoRedirect)
    return opener, jar


def get(opener, path):
    try:
        r = opener.open(BASE + path, timeout=20)
        return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def post(opener, path, data):
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        r = opener.open(req, timeout=20)
        return r.status, r.read().decode("utf-8", "replace"), r.headers.get("Location")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), e.headers.get("Location")


def csrf_of(html):
    m = re.search(r'name="csrf_token" value="([^"]+)"', html)
    return m.group(1) if m else None


def main():
    opener, jar = make_opener()

    status, html = get(opener, "/login")
    token = csrf_of(html)
    record("/login renders with csrf", status == 200 and token is not None, "status=" + str(status))

    status, html, loc = post(
        opener,
        "/register",
        {"name": "Smoke Test", "email": EMAIL, "password": PASSWORD, "password_confirm": PASSWORD, "csrf_token": token},
    )
    record("register redirects", status == 303, "status=" + str(status) + " loc=" + str(loc))

    status, html = get(opener, "/")
    record("home serves logged-in user", status == 200 and "Smoke Test" in html, "status=" + str(status))

    status, html, loc = post(opener, "/logout", {"csrf_token": csrf_of(html) or ""})
    record("logout redirects", status == 303, "status=" + str(status) + " loc=" + str(loc))

    status, html = get(opener, "/")
    record("logged out cannot see home", status == 303, "status=" + str(status))

    opener2, _ = make_opener()
    status, html = get(opener2, "/login")
    token = csrf_of(html)
    status, html, loc = post(opener2, "/login", {"email": EMAIL, "password": "wrong-password", "csrf_token": token})
    record("wrong password rejected", status == 401 and "違います" in html, "status=" + str(status))

    opener3, _ = make_opener()
    status, html = get(opener3, "/login")
    token = csrf_of(html)
    status, html, loc = post(opener3, "/login", {"email": EMAIL, "password": PASSWORD, "csrf_token": token})
    record("correct password logs in", status == 303 and loc == "/", "status=" + str(status) + " loc=" + str(loc))

    opener4, _ = make_opener()
    status, html = get(opener4, "/login")
    token = csrf_of(html)
    status, html, loc = post(
        opener4,
        "/register",
        {"name": "Dup", "email": EMAIL, "password": PASSWORD, "password_confirm": PASSWORD, "csrf_token": token},
    )
    record("duplicate email rejected", status == 400 and "既に登録" in html, "status=" + str(status))

    opener5, _ = make_opener()
    status, html = get(opener5, "/login")
    token = csrf_of(html)
    status, html, loc = post(opener5, "/login", {"email": EMAIL, "password": PASSWORD, "csrf_token": "bogus"})
    record("bad csrf rejected", status == 403, "status=" + str(status))

    opener6, _ = make_opener()
    status, html = get(opener6, "/login")
    token = csrf_of(html)
    status, html, loc = post(
        opener6,
        "/register",
        {"name": "Short", "email": "short@example.com", "password": "abc", "password_confirm": "abc", "csrf_token": token},
    )
    record("short password rejected", status == 400 and "8文字" in html, "status=" + str(status))

    passed = sum(1 for _, p, _ in results if p)
    print()
    print("SCORE " + str(passed) + "/" + str(len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
