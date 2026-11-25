import json
import os
import shutil
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))

from app.receipts import extract
from app.receipts.storage import UPLOAD_ROOT

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FIXTURES = os.environ.get("RECEIPT_FIXTURES") or os.path.join(ROOT, "documents", "_extract", "fixtures")
STAGE = os.path.join(UPLOAD_ROOT, "_extract_fixtures")

passed = 0
failed = []


def check(label, ok, detail=""):
    global passed
    passed += 1 if ok else 0
    print(("PASS " if ok else "FAIL ") + label + ("  " + detail if detail else ""))
    if not ok:
        failed.append(label + "  " + detail)


def staged(name):
    os.makedirs(STAGE, exist_ok=True)
    target = os.path.join(STAGE, name)
    shutil.copyfile(os.path.join(FIXTURES, name), target)
    return "_extract_fixtures/" + name


def read(name):
    result = extract.read_receipt(staged(name))
    print("OBSERVED " + name + "  " + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


payment = read("payment_screenshot.png")
check("payment screenshot counts as a payment", payment.get("is_payment") is True, repr(payment.get("is_payment")))
check("payment screenshot amount is 3200", payment.get("amount") == 3200, repr(payment.get("amount")))
check("payment screenshot date is 2026-11-25", payment.get("date") == "2026-11-25", repr(payment.get("date")))
source = payment.get("source") or ""
check("payment screenshot source is the recipient", "東京電力" in source, repr(payment.get("source")))

note = read("not_payment.png")
check("memo image is not a payment", note.get("is_payment") is False, repr(note.get("is_payment")))
check("memo image has no amount", note.get("amount") is None, repr(note.get("amount")))

print()
print("SCORE " + str(passed) + "/" + str(passed + len(failed)))
sys.exit(0 if not failed else 1)
