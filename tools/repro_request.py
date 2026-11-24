import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))

from app.shared.config import settings

KEY = settings.gemini_api_key
URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    + settings.gemini_model
    + ":generateContent?key="
    + urllib.parse.quote(KEY, safe="")
)

print("key length   " + str(len(KEY)))
print("key prefix   " + KEY[:6] + " ... " + KEY[-4:])
print("url          " + URL[:70] + "..." + URL[-12:])
for name in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "NO_PROXY"):
    if os.environ.get(name):
        print("proxy " + name + "  " + os.environ[name][:60])
print("proxy handler " + str(urllib.request.getproxies()))

body = {
    "systemInstruction": {"parts": [{"text": "You are a test."}]},
    "contents": [{"role": "user", "parts": [{"text": "Say OK"}]}],
    "generationConfig": {"temperature": 0},
}
req = urllib.request.Request(
    URL,
    data=json.dumps(body).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    print("status 200 text=" + text[:40])
except urllib.error.HTTPError as exc:
    print("status " + str(exc.code))
    print(exc.read().decode("utf-8", "replace")[:500])
    sys.exit(1)
