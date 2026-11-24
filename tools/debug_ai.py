import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))

from app.shared import ai
from app.shared.config import settings


def mask(value):
    if not value:
        return "EMPTY"
    if len(value) <= 10:
        return value[:2] + "***"
    return value[:5] + "..." + value[-4:]


def main():
    print("env var present      " + str("GEMINI_API_KEY" in os.environ))
    print("settings key         " + mask(settings.gemini_api_key) + " len=" + str(len(settings.gemini_api_key)))
    print("model                " + settings.gemini_model)
    raw = os.environ.get("GEMINI_API_KEY", "")
    print("env raw key          " + mask(raw) + " len=" + str(len(raw)))
    print("identical            " + str(raw == settings.gemini_api_key))
    print("has whitespace       " + str(raw != raw.strip()))
    print()
    try:
        result = ai.generate("You are a test.", ai.user_turn("Say OK."))
        print("call ok: " + repr(result)[:200])
        return 0
    except ai.AIError as exc:
        print("AIError code=" + str(exc.code))
        print("detail=" + str(exc.detail)[:400])
        return 1


if __name__ == "__main__":
    sys.exit(main())
