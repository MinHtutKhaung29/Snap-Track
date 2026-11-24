import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".env"


def main():
    if len(sys.argv) < 2:
        print("usage: update_env.py KEY_NAME   (value comes from the environment)")
        return 1
    name = sys.argv[1]
    value = os.environ.get(name)
    if not value:
        print("environment variable " + name + " is empty")
        return 1
    lines = ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []
    out = []
    found = False
    for line in lines:
        if line.startswith(name + "="):
            out.append(name + "=" + value)
            found = True
        else:
            out.append(line)
    if not found:
        out.append(name + "=" + value)
    ENV.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("updated " + name + " in .env (length " + str(len(value)) + ")")
    return 0


if __name__ == "__main__":
    sys.exit(main())
