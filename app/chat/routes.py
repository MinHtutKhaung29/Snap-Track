import json

from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.chat import service, tools
from app.shared import auth, csrf, db

router = APIRouter()

COMMITMENT_CARD_TYPES = ("commitment_proposal", "commitment_payment", "commitment")
PENDING_TYPES = ("proposal", "commitment_proposal", "commitment_payment")


def _templates(request):
    return request.app.state.templates


def _uid(user):
    return user["user_id"]


def _decode_payload(row):
    if isinstance(row["payload"], str):
        try:
            row["payload"] = json.loads(row["payload"])
        except ValueError:
            row["payload"] = None
    return row


def _rows_after(uid, after_id):
    rows = db.fetch_all(
        "SELECT message_id, role, body, payload, created_at FROM chat_message "
        "WHERE user_id = %s AND message_id > %s ORDER BY message_id",
        (uid, after_id),
    )
    for row in rows:
        _decode_payload(row)
    return rows


def _render_rows(request, rows, csrf_token):
    categories = db.fetch_all(
        "SELECT code, category_name FROM categories WHERE kind = 'expense' ORDER BY sort_order"
    )
    env = request.app.state.templates.env
    default_partial = env.get_template("_msg.html")
    commitment_partial = env.get_template("_commitment_msg.html")
    html = ""
    for index, row in enumerate(rows):
        payload = row.get("payload")
        partial = (
            commitment_partial
            if isinstance(payload, dict) and payload.get("type") in COMMITMENT_CARD_TYPES
            else default_partial
        )
        html += partial.render(
            m=row,
            csrf_token=csrf_token,
            categories=categories,
            show_time=index == len(rows) - 1 or rows[index + 1]["role"] != row["role"],
        )
    return html


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
        {
            "user": user,
            "messages": messages,
            "categories": categories,
            "today": tools.today_jst(),
            "csrf_token": csrf.issue_token(request),
        },
    )


@router.post("/chat/send")
def chat_send_json(request: Request, message: str = Form(""), csrf_token: str = Form("")):
    csrf.verify_token(request, csrf_token)
    user = auth.current_user(request)
    if user is None:
        return JSONResponse({"ok": False, "error": "auth"}, status_code=401)
    uid = _uid(user)
    before = db.fetch_one(
        "SELECT COALESCE(MAX(message_id), 0) AS m FROM chat_message WHERE user_id = %s", (uid,)
    )
    result = service.handle_turn(uid, message)
    rows = _rows_after(uid, before["m"])
    html = _render_rows(request, rows, csrf_token)
    return JSONResponse({"ok": bool(result.get("ok")), "type": result.get("type"), "html": html})


@router.post("/chat")
def chat_send(request: Request, message: str = Form(""), csrf_token: str = Form("")):
    csrf.verify_token(request, csrf_token)
    user = auth.current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    service.handle_turn(_uid(user), message)
    return RedirectResponse("/chat", status_code=303)


@router.post("/chat/answer/{message_id}")
def chat_answer(request: Request, message_id: int, choice: str = Form(""), csrf_token: str = Form("")):
    csrf.verify_token(request, csrf_token)
    user = auth.current_user(request)
    if user is None:
        return JSONResponse({"ok": False, "error": "auth"}, status_code=401)
    uid = _uid(user)
    row = db.fetch_one(
        "SELECT message_id, role, body, payload, created_at FROM chat_message "
        "WHERE message_id = %s AND user_id = %s",
        (message_id, uid),
    )
    payload = None
    if row and row["payload"]:
        payload = _decode_payload(row)["payload"]
    if (
        choice not in ("yes", "no")
        or not isinstance(payload, dict)
        or payload.get("type") != "question"
        or payload.get("answer") is not None
    ):
        return JSONResponse({"ok": False, "error": "answered"}, status_code=409)
    payload["answer"] = choice
    db.execute(
        "UPDATE chat_message SET payload = %s WHERE message_id = %s AND user_id = %s",
        (json.dumps(payload, ensure_ascii=False), message_id, uid),
    )
    label = payload["yes"] if choice == "yes" else payload["no"]
    service.handle_turn(uid, label)
    card = _decode_payload(
        db.fetch_one(
            "SELECT message_id, role, body, payload, created_at FROM chat_message "
            "WHERE message_id = %s AND user_id = %s",
            (message_id, uid),
        )
    )
    rows = _rows_after(uid, message_id)
    return JSONResponse(
        {
            "ok": True,
            "html": _render_rows(request, rows, csrf_token),
            "card_html": _render_rows(request, [card], csrf_token),
        }
    )


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
        if payload.get("type") in PENDING_TYPES and payload.get("status") == "pending":
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
