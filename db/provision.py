import os
import secrets
import sys
from pathlib import Path

import mysql.connector

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
DB_NAME = "snapandtrack"
APP_USER = "snaptrack"
HOST = os.environ.get("DB_HOST", "127.0.0.1")
PORT = int(os.environ.get("DB_PORT", "3306"))


def read_env():
    values = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def write_env(values):
    lines = [
        "DB_HOST=" + values.get("DB_HOST", HOST),
        "DB_PORT=" + str(values.get("DB_PORT", PORT)),
        "DB_NAME=" + values.get("DB_NAME", DB_NAME),
        "DB_USER=" + values.get("DB_USER", APP_USER),
        "DB_PASSWORD=" + values["DB_PASSWORD"],
        "DB_ROOT_PASSWORD=" + values["DB_ROOT_PASSWORD"],
        "SECRET_KEY=" + values["SECRET_KEY"],
        "GEMINI_API_KEY=" + values.get("GEMINI_API_KEY", ""),
        "GEMINI_MODEL=" + values.get("GEMINI_MODEL", "gemini-3.1-flash-lite"),
        "AI_DAILY_CAP=" + values.get("AI_DAILY_CAP", "200"),
    ]
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def connect(password):
    return mysql.connector.connect(
        host=HOST,
        port=PORT,
        user="root",
        password=password,
        charset="utf8mb4",
        connection_timeout=10,
    )


def main():
    env = read_env()
    env.setdefault("DB_PASSWORD", secrets.token_urlsafe(24))
    env.setdefault("DB_ROOT_PASSWORD", secrets.token_urlsafe(24))
    env.setdefault("SECRET_KEY", secrets.token_urlsafe(32))

    root_password = env.get("DB_ROOT_PASSWORD")
    conn = None
    for candidate in ("", root_password):
        try:
            conn = connect(candidate)
            used = candidate
            break
        except mysql.connector.Error:
            conn = None
    if conn is None:
        print("could not connect as root with either empty or stored password")
        return 1

    cur = conn.cursor()
    cur.execute("ALTER USER 'root'@'localhost' IDENTIFIED BY %s", (root_password,))
    cur.execute("CREATE DATABASE IF NOT EXISTS " + DB_NAME + " CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
    cur.execute("CREATE USER IF NOT EXISTS %s@'localhost' IDENTIFIED BY %s", (APP_USER, env["DB_PASSWORD"]))
    cur.execute("ALTER USER %s@'localhost' IDENTIFIED BY %s", (APP_USER, env["DB_PASSWORD"]))
    cur.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON " + DB_NAME + ".* TO %s@'localhost'", (APP_USER,))
    cur.execute("FLUSH PRIVILEGES")
    conn.commit()

    cur.execute("SELECT VERSION(), @@port, @@bind_address")
    version, port, bind = cur.fetchone()
    cur.execute("SHOW DATABASES LIKE %s", (DB_NAME,))
    db_ok = cur.fetchone() is not None
    cur.close()
    conn.close()

    write_env(env)

    print("mysql          " + version + " on port " + str(port) + " bind " + str(bind))
    print("database       " + DB_NAME + " exists=" + str(db_ok))
    print("app user       " + APP_USER + " password set=" + str(len(env["DB_PASSWORD"]) > 20))
    print("root password  changed from " + ("empty" if used == "" else "stored") + " to stored value")
    print(".env written   " + str(ENV_PATH) + " (gitignored)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
