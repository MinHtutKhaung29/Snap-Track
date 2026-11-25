from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, Environment, FileSystemLoader, select_autoescape
from starlette.middleware.sessions import SessionMiddleware

from app.chat import routes as chat_routes
from app.commitments import routes as commitment_routes
from app.login import routes as login_routes
from app.receipts import routes as receipt_routes
from app.shared import auth, csrf, db
from app.shared.config import settings

BASE = Path(__file__).resolve().parent
TEMPLATE_DIRS = [
    BASE / "shared" / "templates",
    BASE / "login" / "templates",
    BASE / "chat" / "templates",
    BASE / "receipts" / "templates",
    BASE / "commitments" / "templates",
]


def build_templates():
    loaders = [FileSystemLoader(str(d)) for d in TEMPLATE_DIRS if d.is_dir()]
    env = Environment(loader=ChoiceLoader(loaders), autoescape=select_autoescape(["html", "xml"]))
    return Jinja2Templates(env=env)


app = FastAPI(title="Snap & Track", docs_url="/docs", redoc_url=None)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="st_session",
    max_age=settings.session_max_age,
    same_site="lax",
)
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")
app.state.templates = build_templates()
app.include_router(login_routes.router)
app.include_router(chat_routes.router)
app.include_router(receipt_routes.router)
app.include_router(commitment_routes.router)


@app.get("/health")
def health():
    try:
        info = db.health()
    except Exception as exc:
        return JSONResponse({"status": "error", "db": type(exc).__name__}, status_code=503)
    info["status"] = "ok"
    info["model"] = settings.gemini_model
    return info


@app.get("/")
def home(request: Request):
    user = auth.current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    return RedirectResponse("/chat", status_code=303)


@app.get("/status")
def status_page(request: Request):
    user = auth.current_user(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    try:
        info = db.health()
    except Exception:
        info = {"version": "unreachable", "tables": 0}
    info["model"] = settings.gemini_model
    return app.state.templates.TemplateResponse(
        request,
        "home.html",
        {"user": user, "health": info, "csrf_token": csrf.issue_token(request)},
    )
