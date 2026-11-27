import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.chat.service import SYSTEM
from app.chat.tools import TOOL_DECLS
from app.shared.config import settings

URL = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s"
REAL = {
    "systemInstruction": {"parts": [{"text": SYSTEM}]},
    "tools": [{"functionDeclarations": TOOL_DECLS}],
}


def call(budget, real=False):
    body = {
        "contents": [{"role": "user", "parts": [{"text": "ランチ 850円"}]}],
        "generationConfig": {"temperature": 0},
    }
    if real:
        body.update(REAL)
    if budget is not None:
        body["generationConfig"]["thinkingConfig"] = {"thinkingBudget": budget}
    req = urllib.request.Request(
        URL % (settings.gemini_model, settings.gemini_api_key),
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    start = time.time()
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode())
    usage = data.get("usageMetadata", {})
    return time.time() - start, usage.get("thoughtsTokenCount"), usage.get("candidatesTokenCount")


print("system_chars=%d tool_chars=%d" % (len(SYSTEM), len(json.dumps(TOOL_DECLS))))
for label, budget, real in (("bare", None, False), ("bare_budget0", 0, False), ("real", None, True), ("real_budget0", 0, True)):
    try:
        seconds, thoughts, out = call(budget, real)
        print("%s seconds=%.2f thoughts=%s out=%s" % (label, seconds, thoughts, out))
    except Exception as exc:
        print("%s error=%s %s" % (label, type(exc).__name__, exc))
