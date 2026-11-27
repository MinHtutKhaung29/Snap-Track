import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))

from app.receipts.routes import _card_state

passed = 0
failed = []


def check(label, ok, detail=""):
    global passed
    passed += 1 if ok else 0
    print(("PASS " if ok else "FAIL ") + label + ("  " + detail if detail else ""))
    if not ok:
        failed.append(label + "  " + detail)


item = {
    "is_payment": False,
    "evidence_type": "other",
    "amount": None,
    "date": None,
    "source": "ユニクロ",
    "category_code": "other",
}
state = _card_state(item, {})
check("an item photo asks instead of dead-ending", state["mode"] == "ask", state["mode"])
check("an item photo asks for the price", state["want_amount"] is True, repr(state["want_amount"]))
check("an item photo never shows an amount", state["display_amount"] is None, repr(state["display_amount"]))

menu = dict(item, amount=1200, date="2026-11-20", source="ランチメニュー", category_code="food")
state = _card_state(menu, {})
check("a price list is never ready to save", state["mode"] == "ask", state["mode"])
check("a price list price is not pre-filled", state["display_amount"] is None, repr(state["display_amount"]))

typed = _card_state(item, {"amount": "5800"})
check("the price he types becomes the amount", typed["display_amount"] == 5800, repr(typed["display_amount"]))
check("a missing date is still asked for", typed["mode"] == "ask" and typed["want_date"] is True, str(typed["mode"]) + " " + str(typed["want_date"]))

typed = _card_state(dict(item, date="2026-11-26"), {"amount": "5800"})
check("an item photo is confirmed, never auto-saved", typed["mode"] == "ask", typed["mode"])
check("an item photo stops asking for the price", typed["want_amount"] is False, repr(typed["want_amount"]))

receipt = {
    "is_payment": True,
    "evidence_type": "receipt",
    "amount": 1280,
    "date": "2026-11-25",
    "source": "セブン-イレブン",
    "category_code": "food",
}
state = _card_state(receipt, {})
check("a readable receipt stays ready", state["mode"] == "ready", state["mode"])
check("a readable receipt keeps its amount", state["display_amount"] == 1280, repr(state["display_amount"]))

state = _card_state(receipt, {"amount": "999"})
check("a corrected amount wins over the reading", state["display_amount"] == 999, repr(state["display_amount"]))

state = _card_state(receipt, {}, force_ask=True)
check("manual entry forces the ask screen", state["mode"] == "ask", state["mode"])

print()
print("SCORE " + str(passed) + "/" + str(passed + len(failed)))
sys.exit(0 if not failed else 1)
