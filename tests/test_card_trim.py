import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))

from app.main import app
from app.shared import db

passed = 0
failed = []


def check(label, ok, detail=""):
    global passed
    passed += 1 if ok else 0
    print(("PASS " if ok else "FAIL ") + label + ("  " + detail if detail else ""))
    if not ok:
        failed.append(label + "  " + detail)


env = app.state.templates.env
categories = db.fetch_all("SELECT code, category_name FROM categories WHERE kind = 'expense' ORDER BY sort_order")


def render(preview):
    row = {
        "message_id": 1,
        "role": "assistant",
        "body": "この内容で記録しますか？",
        "payload": {"type": "proposal", "status": "pending", "tool": "record_expense", "preview": preview},
        "created_at": datetime(2026, 11, 26, 12, 34),
    }
    return env.get_template("_msg.html").render(
        m=row, csrf_token="test", categories=categories, show_time=True
    )


PAST = {
    "kind": "expense",
    "amount": 1200,
    "date": "2026-11-20",
    "source": "ランチ",
    "category": "食費",
    "date_label": "2026年11月20日（金）",
    "date_short": "11/20",
    "is_today": False,
    "reason": "date_inferred",
}
TODAY = dict(PAST, date="2026-11-26", date_label="2026年11月26日（木）", date_short="11/26", is_today=True, reason=None)
NOAMOUNT = dict(TODAY, reason="amount_not_in_message")

past = render(PAST)
check("the past card carries the short date", "11/20" in past, past[past.find("11/"):][:12])
check("the past card drops the long date", "2026年" not in past)
check("one info line, no stacked meta rows", past.count('class="meta"') == 0 and past.count('class="line"') == 1)
check("amount, category and source sit in that line", "¥1,200" in past and "食費" in past and "ランチ" in past)
check("one short warning", 'class="warn"' in past and "日付は推測です" in past, str(past.count('class="warn"')))
check("the warning no longer explains the fix", "違っていれば" not in past)
check("the hint text is gone", past.count("swipe-hint") == 0, str(past.count("swipe-hint")))
check("the card shows drag stamps instead", 'data-stamp="right"' in past and 'data-stamp="left"' in past)
check("both buttons survive", past.count("swipe-btn") == 2, str(past.count("swipe-btn")))
check("直す is gone", "直す" not in past)
check("the card asks to be floated", 'data-modal="confirm"' in past)

today = render(TODAY)
check("today's card hides the date", "11/26" not in today and "2026年" not in today)
check("today's card keeps the amount", "¥1,200" in today)

noamount = render(NOAMOUNT)
check("a card without an amount says so", "金額がメッセージにありません" in noamount)

print()
print("SCORE " + str(passed) + "/" + str(passed + len(failed)))
sys.exit(0 if not failed else 1)
