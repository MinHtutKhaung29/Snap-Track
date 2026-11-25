import base64
import json
import os

from app.receipts.storage import absolute_path
from app.shared import ai

SYSTEM = (
    "You are a receipt reader for a Japanese personal expense tracker. "
    "You extract facts from a photo of a Japanese receipt. "
    "You never guess: if a value cannot be read with certainty, return null for it."
)

PROMPT = (
    "Read this receipt image and return the fields.\n"
    "- amount = the final total the customer paid including tax (合計 / お買上金額 / 総計 / 領収金額). "
    "Never return 小計, a single line item, the tax line, 預り, or 釣銭.\n"
    "- amount must be a whole number of yen.\n"
    "- date = purchase date as YYYY-MM-DD. Japanese eras: 令和 = 2018 + n, 平成 = 1988 + n, 昭和 = 1925 + n. "
    "If no date is readable, return null.\n"
    "- shop = the store or restaurant name as printed, without the address and without 御中/様.\n"
    "- category_code is exactly one of food, transport, daily, social, utility, other.\n"
    "- is_receipt = false when the image is not a receipt.\n"
    "- If the image holds several different receipts or the total is unclear, return null for it. Never invent a digit."
)

CATEGORY_CODES = ["food", "transport", "daily", "social", "utility", "other"]

SCHEMA = {
    "type": "object",
    "properties": {
        "is_receipt": {"type": "boolean"},
        "date": {"type": "string", "nullable": True},
        "shop": {"type": "string", "nullable": True},
        "amount": {"type": "integer", "nullable": True},
        "category_code": {"type": "string", "enum": CATEGORY_CODES},
    },
    "required": ["is_receipt", "date", "shop", "amount", "category_code"],
}


def read_receipt(relative_path):
    path = absolute_path(relative_path)
    if not os.path.exists(path):
        raise ai.AIError("missing_file", relative_path)
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    body_contents = [
        {
            "role": "user",
            "parts": [
                {"text": PROMPT},
                {"inline_data": {"mime_type": "image/jpeg", "data": data}},
            ],
        }
    ]
    result = ai.generate_raw(SYSTEM, body_contents, schema=SCHEMA)
    return json.loads(result)
