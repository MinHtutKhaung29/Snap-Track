import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.chat.service import SYSTEM
from app.shared import ai
from app.shared.config import settings

print("model=" + settings.gemini_model)
print("mode=" + settings.ai_mode)

for label, system, user in (
    ("tiny", "You are a test.", "say ok"),
    ("system", SYSTEM, "ランチ 850円"),
):
    start = time.time()
    try:
        out = ai.generate(system, [ai.user_turn(user)])
        text = (out.get("text") or "").replace("\n", " ")[:40]
        print(label + " seconds=%.2f calls=%d reply=%r" % (time.time() - start, len(out.get("calls") or []), text))
    except Exception as exc:
        print(label + " seconds=%.2f error=%s %s" % (time.time() - start, type(exc).__name__, exc))
