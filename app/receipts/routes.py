import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse

from app.chat import tools as toolbox
from app.receipts import extract, storage
from app.shared import auth, csrf, db
from app.shared.format import jp_date

router = APIRouter()
JST = timezone(timedelta(hours=9))

ERROR_MESSAGES = {
    "missing_date": "日付を入れてください",
    "invalid": "入力内容を確認してください",
    "upload": "画像を読み込めませんでした（5MBまで）",
    "too_large": "画像が大きすぎます（5MBまで）",
    "not_an_image": "画像ファイルではありません",
}

QUEUE_SQL = (
    "SELECT r.receipt_id, r.image_path, r.uploaded_at, r.read_status, r.extracted "
    "FROM receipts r WHERE r.user_id = %s AND r.discarded_at IS NULL "
    "AND r.read_status IN ('done','failed') "
    "AND NOT EXISTS (SELECT 1 FROM transactions t WHERE t.receipt_id = r.receipt_id AND t.deleted_at IS NULL) "
    "ORDER BY r.uploaded_at"
)


def _templates(request):
    return request.app.state.templates


def _categories():
    return db.fetch_all("SELECT code, category_name FROM categories WHERE kind = 'expense' ORDER BY sort_order")


def _pending(user_id):
    rows = db.fetch_all(QUEUE_SQL, (user_id,))
    for row in rows:
        data = row["extracted"]
        if isinstance(data, str):
            try:
                row["data"] = json.loads(data)
            except ValueError:
                row["data"] = {}
        else:
            row["data"] = data or {}
    return rows


@router.get("/receipts")
def queue(request: Request):
    user = auth.current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    error_code = request.query_params.get("error", "")
    error_message = ERROR_MESSAGES.get(error_code)
    if error_code and error_message is None:
        error_message = ERROR_MESSAGES["invalid"]
    return _render_queue(request, user, error_message=error_message)


def _render_queue(request, user, error_message=None, override=None, status_code=200):
    categories = _categories()
    cat_map = {c["code"]: c["category_name"] for c in categories}
    rows = _pending(user["user_id"])
    card = rows[0] if rows else None
    if card:
        if card["data"].get("date"):
            try:
                card["date_label"] = jp_date(card["data"]["date"])
            except Exception:
                card["date_label"] = card["data"]["date"]
        code = card["data"].get("category_code") or "other"
        card["category_name"] = cat_map.get(code) or cat_map.get("other") or code
        chosen_code = (override or {}).get("category_code") or code
        card["display_category"] = cat_map.get(chosen_code) or card["category_name"]
        typed_amount = (override or {}).get("amount")
        card["display_amount"] = int(typed_amount) if str(typed_amount or "").isdigit() else card["data"].get("amount")
        card["edited"] = bool(typed_amount)
    return _templates(request).TemplateResponse(
        request,
        "receipts.html",
        {
            "user": user,
            "card": card,
            "index": 1 if card else 0,
            "total": len(rows),
            "categories": categories,
            "today": toolbox.today_jst().isoformat(),
            "error_message": error_message,
            "override": override or {},
            "csrf_token": csrf.issue_token(request),
        },
        status_code=status_code,
    )


@router.post("/receipts/upload")
async def upload(request: Request, photo: UploadFile = File(None), csrf_token: str = Form("")):
    csrf.verify_token(request, csrf_token)
    user = auth.current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    if photo is None:
        return RedirectResponse("/receipts", status_code=303)
    data = await photo.read()
    try:
        relative, size, dimensions = storage.save_receipt_image(data)
    except storage.UploadError as exc:
        code = str(exc) if str(exc) in ("too_large", "not_an_image") else "upload"
        return RedirectResponse(f"/receipts?error={code}", status_code=303)
    receipt_id = db.execute(
        "INSERT INTO receipts (user_id, image_path, read_status) VALUES (%s, %s, 'processing')",
        (user["user_id"], relative),
    )
    try:
        result = extract.read_receipt(relative)
    except Exception as exc:
        detail = str(getattr(exc, "code", type(exc).__name__))[:120]
        db.execute(
            "UPDATE receipts SET read_status = 'failed', extracted = %s WHERE receipt_id = %s AND user_id = %s",
            (json.dumps({"error": detail}, ensure_ascii=False), receipt_id, user["user_id"]),
        )
        return RedirectResponse("/receipts", status_code=303)
    db.execute(
        "UPDATE receipts SET read_status = 'done', extracted = %s WHERE receipt_id = %s AND user_id = %s",
        (json.dumps(result, ensure_ascii=False), receipt_id, user["user_id"]),
    )
    return RedirectResponse("/receipts", status_code=303)


@router.get("/receipts/{receipt_id}/image")
def image(request: Request, receipt_id: int):
    user = auth.current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    row = db.fetch_one(
        "SELECT image_path FROM receipts WHERE receipt_id = %s AND user_id = %s",
        (receipt_id, user["user_id"]),
    )
    if not row:
        return RedirectResponse("/receipts", status_code=303)
    try:
        path = storage.absolute_path(row["image_path"])
    except storage.UploadError:
        return RedirectResponse("/receipts", status_code=303)
    return FileResponse(path, media_type="image/jpeg")


@router.post("/receipts/{receipt_id}/save")
def save(
    request: Request,
    receipt_id: int,
    amount: str = Form(""),
    date: str = Form(""),
    shop: str = Form(""),
    category_code: str = Form(""),
    csrf_token: str = Form(""),
):
    csrf.verify_token(request, csrf_token)
    user = auth.current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    row = db.fetch_one(
        "SELECT receipt_id, extracted FROM receipts WHERE receipt_id = %s AND user_id = %s AND discarded_at IS NULL",
        (receipt_id, user["user_id"]),
    )
    if not row:
        return RedirectResponse("/receipts", status_code=303)
    stored = row["extracted"]
    if isinstance(stored, str):
        try:
            stored = json.loads(stored)
        except ValueError:
            stored = {}
    stored = stored or {}
    kept = {"amount": amount, "date": date, "shop": shop, "category_code": category_code}
    resolved_date = (date or "").strip() or str(stored.get("date") or "").strip()
    if not resolved_date:
        return _render_queue(
            request, user, error_message=ERROR_MESSAGES["missing_date"], override=kept, status_code=400
        )
    args = {
        "amount": amount or stored.get("amount"),
        "date": resolved_date,
        "source": shop or stored.get("shop"),
        "category_code": category_code or stored.get("category_code") or "other",
    }
    try:
        normalized = toolbox.validate("record_expense", args)
    except toolbox.ToolError:
        return _render_queue(
            request, user, error_message=ERROR_MESSAGES["invalid"], override=kept, status_code=400
        )
    saved = toolbox.execute("record_expense", normalized, user["user_id"])
    db.execute(
        "UPDATE transactions SET receipt_id = %s, source_kind = 'photo' WHERE txn_id = %s AND user_id = %s",
        (receipt_id, saved["txn_id"], user["user_id"]),
    )
    return RedirectResponse("/receipts", status_code=303)


@router.post("/receipts/{receipt_id}/discard")
def discard(request: Request, receipt_id: int, csrf_token: str = Form("")):
    csrf.verify_token(request, csrf_token)
    user = auth.current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    db.execute(
        "UPDATE receipts SET discarded_at = NOW() WHERE receipt_id = %s AND user_id = %s AND discarded_at IS NULL",
        (receipt_id, user["user_id"]),
    )
    return RedirectResponse("/receipts", status_code=303)
