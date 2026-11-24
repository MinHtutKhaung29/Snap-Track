import json

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.chat import service
from app.chat import tools as toolbox
from app.shared import auth, csrf, db

router = APIRouter()


def _templates(request):
    return request.app.state.templates


def _uid(user):
    return user["user_id"]


@router.get("/chat")
def chat_page(request: Request):
    user = auth.current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    messages = service.thread(_uid(user))
    categories = db.fetch_all(
        "SELECT code, category_name FROM categories WHERE kind = 'expense' ORDER BY sort_order"
    )
    return _templates(request).TemplateResponse(
        request,
        "chat.html",
        {"user": user, "messages": messages, "categories": categories, "csrf_token": csrf.issue_token(request)},
    )


@router.post("/chat")
def chat_send(request: Request, message: str = Form(""), csrf_token: str = Form("")):
    csrf.verify_token(request, csrf_token)
    user = auth.current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    service.handle_turn(_uid(user), message)
    return RedirectResponse("/chat", status_code=303)


@router.post("/chat/confirm/{message_id}")
def chat_confirm(
    request: Request,
    message_id: int,
    amount: str = Form(""),
    date: str = Form(""),
    category_code: str = Form(""),
    csrf_token: str = Form(""),
):
    csrf.verify_token(request, csrf_token)
    user = auth.current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    row = db.fetch_one(
        "SELECT message_id, payload FROM chat_message WHERE message_id = %s AND user_id = %s",
        (message_id, _uid(user)),
    )
    if not row or not row["payload"]:
        return RedirectResponse("/chat", status_code=303)
    payload = json.loads(row["payload"]) if isinstance(row["payload"], str) else row["payload"]
    if payload.get("type") != "proposal" or payload.get("status") != "pending":
        return RedirectResponse("/chat", status_code=303)
    raw_args = dict(payload.get("raw_args") or {})
    if amount.strip():
        raw_args["amount"] = amount.strip()
    if date.strip():
        raw_args["date"] = date.strip()
    if category_code.strip():
        raw_args["category_code"] = category_code.strip()
    try:
        normalized = toolbox.validate(payload["tool"], raw_args)
        saved = toolbox.execute(payload["tool"], normalized, _uid(user))
    except toolbox.ToolError:
        db.execute(
            "UPDATE chat_message SET payload = %s WHERE message_id = %s AND user_id = %s",
            (json.dumps({"type": "error", "code": "invalid"}, ensure_ascii=False), message_id, _uid(user)),
        )
        return RedirectResponse("/chat", status_code=303)
    body = "記録しました: " + service.describe(saved)
    db.execute(
        "UPDATE chat_message SET body = %s, payload = %s WHERE message_id = %s AND user_id = %s",
        (body, json.dumps({"type": "saved", "txn": saved}, ensure_ascii=False), message_id, _uid(user)),
    )
    return RedirectResponse("/chat", status_code=303)

@router.post("/chat/cancel/{message_id}")
def chat_cancel(request: Request, message_id: int, csrf_token: str = Form("")):
    csrf.verify_token(request, csrf_token)
    user = auth.current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    row = db.fetch_one(
        "SELECT payload FROM chat_message WHERE message_id = %s AND user_id = %s",
        (message_id, _uid(user)),
    )
    if row and row["payload"]:
        payload = json.loads(row["payload"]) if isinstance(row["payload"], str) else row["payload"]
        if payload.get("type") == "proposal" and payload.get("status") == "pending":
            payload["status"] = "canceled"
            db.execute(
                "UPDATE chat_message SET body = %s, payload = %s WHERE message_id = %s AND user_id = %s",
                ("キャンセルしました。", json.dumps(payload, ensure_ascii=False), message_id, _uid(user)),
            )
    return RedirectResponse("/chat", status_code=303)


@router.post("/undo/{txn_id}")
def undo(request: Request, txn_id: int, csrf_token: str = Form("")):
    csrf.verify_token(request, csrf_token)
    user = auth.current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    db.execute(
        "UPDATE transactions SET deleted_at = NOW() WHERE txn_id = %s AND user_id = %s AND deleted_at IS NULL",
        (txn_id, _uid(user)),
    )
    row = db.fetch_one(
        "SELECT message_id, payload FROM chat_message WHERE user_id = %s "
        "AND JSON_EXTRACT(payload, '$.txn.txn_id') = %s ORDER BY message_id DESC LIMIT 1",
        (_uid(user), txn_id),
    )
    if row:
        payload = json.loads(row["payload"]) if isinstance(row["payload"], str) else row["payload"]
        payload["type"] = "undone"
        db.execute(
            "UPDATE chat_message SET body = %s, payload = %s WHERE message_id = %s AND user_id = %s",
            ("取り消しました。", json.dumps(payload, ensure_ascii=False), row["message_id"], _uid(user)),
        )
    return RedirectResponse("/chat", status_code=303)
