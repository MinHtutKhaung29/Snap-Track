import re
from datetime import date

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.commitments import store
from app.shared import auth, csrf, db

router = APIRouter()

ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
UINT_TEXT = re.compile(r"[0-9]{1,10}\Z")

ERROR_TEXT = {
    "not_found": "対象の支払い予定が見つかりません。",
    "not_active": "この支払い予定は完了しています。",
    "stale": "予定が更新されました。もう一度確認してください。",
    "early": "支払期日はまだ来ていません。",
    "invalid": "支払いを記録できませんでした。",
}

ERROR_CODES = {
    "commitment not found": "not_found",
    "commitment is not active": "not_active",
    "payment is stale": "stale",
    "payment is not due yet": "early",
}


def view_rows(user_id, today):
    rows = []
    for item in store.list_commitments(user_id, "active"):
        item["last_txn_id"] = store.latest_txn_id(user_id, item["id"])
        item["is_due"] = item["next_due_date"] <= today
        item["overdue"] = item["next_due_date"] < today
        item["next_due_date"] = item["next_due_date"].isoformat()
        rows.append(item)
    return rows


def snapshot(due_text, last_text):
    if not ISO_DATE.fullmatch(due_text or "") or not UINT_TEXT.fullmatch(last_text or ""):
        return None
    try:
        due = date.fromisoformat(due_text)
    except ValueError:
        return None
    return due, int(last_text)


@router.get("/commitments")
def due_page(request: Request):
    user = auth.current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    note = None
    error_message = None
    paid = request.query_params.get("paid") or ""
    code = request.query_params.get("error") or ""
    if UINT_TEXT.fullmatch(paid):
        note = "支払いを記録しました。"
    if code in ERROR_TEXT:
        error_message = ERROR_TEXT[code]
    return request.app.state.templates.TemplateResponse(
        request,
        "commitments.html",
        {
            "user": user,
            "rows": view_rows(user["user_id"], store.today_jst()),
            "note": note,
            "error_message": error_message,
            "csrf_token": csrf.issue_token(request),
        },
    )


@router.post("/commitments/{commitment_id}/pay")
def pay(
    request: Request,
    commitment_id: int,
    expected_due_date: str = Form(""),
    expected_last_txn_id: str = Form(""),
    csrf_token: str = Form(""),
):
    csrf.verify_token(request, csrf_token)
    user = auth.current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    expected = snapshot(expected_due_date, expected_last_txn_id)
    if expected is None:
        return RedirectResponse("/commitments?error=invalid", status_code=303)
    try:
        with db.cursor(commit=True) as cur:
            saved = store.mark_paid(cur, user["user_id"], commitment_id, expected[0], expected[1], "manual")
    except store.CommitmentError as exc:
        code = ERROR_CODES.get(str(exc), "invalid")
        return RedirectResponse("/commitments?error=" + code, status_code=303)
    return RedirectResponse("/commitments?paid=" + str(saved["txn_id"]), status_code=303)
