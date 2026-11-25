import base64
import json
import os

from app.receipts.storage import absolute_path
from app.shared import ai

SYSTEM = (
    "You read payment evidence for a Japanese personal expense tracker. "
    "The image may be a paper receipt, a photo of one, a screenshot of a payment app, "
    "a bank transfer confirmation, an order confirmation, or an invoice. "
    "You extract what is actually visible and never guess: a value you cannot read is null."
)

PROMPT = (
    "Extract the payment details from this image.\n"
    "- amount: the final amount the user paid, tax included, in whole yen. "
    "On a receipt that is 合計 / お買上金額 / 総計 / 領収金額, never 小計, a line item, the tax line, 預り or 釣銭. "
    "On a screenshot it is the transferred or charged amount, labelled 金額 / 合計 / 支払金額 / 送金額 / charged. "
    "Ignore balances, points, fees that were not charged, and account totals.\n"
    "- date: the payment date as YYYY-MM-DD. Japanese eras: 令和 = 2018 + n, 平成 = 1988 + n, 昭和 = 1925 + n. "
    "A screenshot often shows a timestamp; use its date only.\n"
    "- source: who was paid, as printed — a shop, a person, a service, a utility, an app name. "
    "For a transfer screenshot use the recipient. Never the user's own name.\n"
    "- category_code: exactly one of food, transport, daily, social, utility, other.\n"
    "- evidence_type: receipt, screenshot, invoice, or other.\n"
    "- is_payment: true when the image shows money the user actually paid. "
    "A receipt, a payment screenshot, a transfer confirmation are true. "
    "A shopping cart before payment, a price list, a menu, a bank balance, or a chat message is false.\n"
    "- If several different payments appear, use the largest single completed one and say so in note.\n"
    "Return null for any field you cannot read. Never invent a digit."
)

CATEGORY_CODES = ["food", "transport", "daily", "social", "utility", "other"]

SCHEMA = {
    "type": "object",
    "properties": {
        "is_payment": {"type": "boolean"},
        "evidence_type": {"type": "string", "enum": ["receipt", "screenshot", "invoice", "other"]},
        "date": {"type": "string", "nullable": True},
        "source": {"type": "string", "nullable": True},
        "amount": {"type": "integer", "nullable": True},
        "category_code": {"type": "string", "enum": CATEGORY_CODES},
        "note": {"type": "string", "nullable": True},
    },
    "required": ["is_payment", "evidence_type", "date", "source", "amount", "category_code"],
}


def read_receipt(relative_path):
    path = absolute_path(relative_path)
    if not os.path.exists(path):
        raise ai.AIError("missing_file", relative_path)
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    contents = [
        {
            "role": "user",
            "parts": [
                {"text": PROMPT},
                {"inline_data": {"mime_type": "image/jpeg", "data": data}},
            ],
        }
    ]
    raw = ai.generate_raw(SYSTEM, contents, schema=SCHEMA)
    return json.loads(raw)
