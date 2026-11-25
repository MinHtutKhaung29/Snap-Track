import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))

from app.chat import tools

CASES = [
    ("今日 ランチ 850円", 850, "2026-11-24", None),
    ("ランチ 850", 850, "2026-11-24", "date_inferred"),
    ("1,200円 のランチ", 1200, "2026-11-24", "date_inferred"),
    ("¥850 コーヒー", 850, "2026-11-24", "date_inferred"),
    ("今日 3個買って 300円", 300, "2026-11-24", None),
    ("2025-11-20 ランチ", 2025, "2025-11-20", "amount_not_in_message"),
    ("今日 10%引きで 999円", 10, "2026-11-24", "amount_not_in_message"),
    ("今日 3個買って 300円", 3, "2026-11-24", "amount_not_in_message"),
    ("11/20 ランチ 900円", 900, "2026-11-20", None),
    ("先週 ランチ 1200円", 1200, "2026-11-17", "date_inferred"),
    ("今月 ランチ 1200円", 1200, "2026-11-10", "date_inferred"),
    ("11月20日 ランチ 900円", 900, "2026-11-20", None),
    ("１２月１日 ランチ ８５０円", 850, "2026-12-01", None),
    ("2026-11-20 ランチ 900円", 900, "2026-11-20", None),
]

passed = 0
failed = []

for text, amount, date, expected in CASES:
    args = {"amount": amount, "date": date, "category_code": "food"}
    got = tools.needs_confirmation("record_expense", args, text)
    ok = got == expected
    passed += 1 if ok else 0
    print(("PASS " if ok else "FAIL ") + repr(text) + "  amount=" + str(amount) + "  got=" + str(got) + "  want=" + str(expected))
    if not ok:
        failed.append((text, amount, got, expected))

query = tools.needs_confirmation("query_money", {"from": "2026-11-01", "to": "2026-11-24", "kind": "expense"}, "今月の食費いくら?")
ok = query is None
passed += 1 if ok else 0
print(("PASS " if ok else "FAIL ") + "query never needs confirmation")
if not ok:
    failed.append(("query", None, query, None))

total = len(CASES) + 1
print()
print("SCORE " + str(passed) + "/" + str(total))
sys.exit(0 if passed == total else 1)
