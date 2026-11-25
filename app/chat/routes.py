import json

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.chat import service
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
    service.confirm(
        _uid(user),
        message_id,
        {"amount": amount, "date": date, "category_code": category_code},
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
    service.undo_transaction(_uid(user), txn_id)
    return RedirectResponse("/chat", status_code=303)
