import hmac
import secrets

from fastapi import HTTPException, Request

SESSION_TOKEN_KEY = "_csrf"


def issue_token(request):
    token = request.session.get(SESSION_TOKEN_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        request.session[SESSION_TOKEN_KEY] = token
    return token


def verify_token(request, submitted):
    expected = request.session.get(SESSION_TOKEN_KEY)
    if not expected or not submitted:
        raise HTTPException(status_code=403, detail="csrf")
    if not hmac.compare_digest(str(expected), str(submitted)):
        raise HTTPException(status_code=403, detail="csrf")
    return True
