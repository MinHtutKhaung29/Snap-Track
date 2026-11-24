from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.shared import auth, csrf

router = APIRouter()

ERRORS = {
    "invalid_credentials": "メールアドレスかパスワードが違います。",
    "name_required": "名前を入力してください。",
    "email_invalid": "メールアドレスの形式が正しくありません。",
    "password_short": "パスワードは8文字以上にしてください。",
    "password_mismatch": "パスワードが一致しません。",
    "email_taken": "このメールアドレスは既に登録されています。",
}


@router.get("/login")
def login_form(request: Request):
    user = auth.current_user(request)
    if user:
        return RedirectResponse("/", status_code=303)
    return request.app.state.templates.TemplateResponse(
        request,
        "login.html",
        {"csrf_token": csrf.issue_token(request), "error": None, "email": ""},
    )


@router.post("/login")
def login_submit(
    request: Request,
    email: str = Form(""),
    password: str = Form(""),
    csrf_token: str = Form(""),
):
    csrf.verify_token(request, csrf_token)
    user = auth.authenticate(email, password)
    if user is None:
        return request.app.state.templates.TemplateResponse(
            request,
            "login.html",
            {"csrf_token": csrf.issue_token(request), "error": ERRORS["invalid_credentials"], "email": email},
            status_code=401,
        )
    auth.login_user(request, user)
    return RedirectResponse("/", status_code=303)


@router.get("/register")
def register_form(request: Request):
    if auth.current_user(request):
        return RedirectResponse("/", status_code=303)
    return request.app.state.templates.TemplateResponse(
        request,
        "register.html",
        {"csrf_token": csrf.issue_token(request), "error": None, "name": "", "email": ""},
    )


@router.post("/register")
def register_submit(
    request: Request,
    name: str = Form(""),
    email: str = Form(""),
    password: str = Form(""),
    password_confirm: str = Form(""),
    csrf_token: str = Form(""),
):
    csrf.verify_token(request, csrf_token)
    if password != password_confirm:
        code = "password_mismatch"
    else:
        code = None
    if code is None:
        try:
            auth.create_user(name, email, password)
        except ValueError as exc:
            code = str(exc)
    if code:
        return request.app.state.templates.TemplateResponse(
            request,
            "register.html",
            {
                "csrf_token": csrf.issue_token(request),
                "error": ERRORS.get(code, "登録できませんでした。"),
                "name": name,
                "email": email,
            },
            status_code=400,
        )
    user = auth.authenticate(email, password)
    if user:
        auth.login_user(request, user)
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
def logout_submit(request: Request, csrf_token: str = Form("")):
    csrf.verify_token(request, csrf_token)
    auth.logout_user(request)
    return RedirectResponse("/login", status_code=303)
