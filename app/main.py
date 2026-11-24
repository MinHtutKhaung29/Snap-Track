from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.shared import db
from app.shared.config import settings

BASE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE / "shared" / "templates"))

app = FastAPI(title="Snap & Track", docs_url="/docs", redoc_url=None)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    session_cookie="st_session",
    max_age=settings.session_max_age,
    same_site="lax",
)
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")


@app.get("/health")
def health():
    try:
        info = db.health()
    except Exception as exc:
        return JSONResponse({"status": "error", "db": str(type(exc).__name__)}, status_code=503)
    info["status"] = "ok"
    info["model"] = settings.gemini_model
    return info


@app.get("/")
def home(request: Request):
    try:
        info = db.health()
    except Exception:
        info = {"version": "unreachable", "tables": 0}
    info["model"] = settings.gemini_model
    return templates.TemplateResponse(request, "home.html", {"health": info})
