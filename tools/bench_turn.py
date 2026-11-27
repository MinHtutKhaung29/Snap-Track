import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.chat import service
from app.shared import db
from app.shared.config import settings

MESSAGES = [
    "ランチ 850円",
    "電車で 210円",
    "昨日 カフェ 600円",
    "コンビニ 480円",
    "先週の食費は？",
    "ドラッグストア 1200円",
    "5000円 もらった",
    "電気 4800円",
    "今月いくら使った？",
    "バス 220円",
]


def bench_user():
    row = db.fetch_one("SELECT user_id FROM users WHERE email = %s", ("bench@example.com",))
    if row:
        return row["user_id"]
    return db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
        ("計測 ユーザー", "bench@example.com", "x"),
    )


def p(values, q):
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * q))))
    return ordered[index]


def main():
    user_id = bench_user()
    rows = []
    for index, message in enumerate(MESSAGES):
        started = time.perf_counter()
        result = service.handle_turn(user_id, message)
        wall = round((time.perf_counter() - started) * 1000)
        timings = dict(service.LAST_TIMINGS)
        rows.append((message, wall, timings))
        print("run %d %s wall=%dms model=%sms history=%sms ok=%s"
              % (index + 1, message, wall, timings.get("model_ms"), timings.get("history_ms"), result.get("ok")))
    steady = rows[1:]
    walls = [row[1] for row in steady]
    models = [row[2].get("model_ms") or 0 for row in steady]
    print("model=%s thinking=%r samples=%d" % (settings.gemini_model, settings.gemini_thinking, len(steady)))
    print("wall p50=%d p95=%d min=%d max=%d" % (p(walls, 0.5), p(walls, 0.95), min(walls), max(walls)))
    print("model p50=%d p95=%d min=%d max=%d mean=%d"
          % (p(models, 0.5), p(models, 0.95), min(models), max(models), statistics.mean(models)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
