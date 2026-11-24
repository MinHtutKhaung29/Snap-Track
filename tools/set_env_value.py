import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".env"


def main():
    if len(sys.argv) < 3:
        print("usage: set_env_value.py NAME VALUE")
        return 1
    name, value = sys.argv[1], sys.argv[2]
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
    print(name + " set to ..." + value[-4:] + " (length " + str(len(value)) + ")")
    return 0


if __name__ == "__main__":
    sys.exit(main())
