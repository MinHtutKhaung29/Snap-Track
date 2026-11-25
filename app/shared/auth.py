import hashlib
import hmac
import secrets

import mysql.connector
from fastapi.responses import RedirectResponse

from app.shared import db
from app.shared.csrf import SESSION_TOKEN_KEY

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 32
SESSION_USER_KEY = "uid"


def hash_password(password):
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=SCRYPT_DKLEN
    )
    return "scrypt${}${}${}${}${}".format(SCRYPT_N, SCRYPT_R, SCRYPT_P, salt.hex(), derived.hex())


def verify_password(password, stored):
    if not stored or not isinstance(stored, str):
        return False
    try:
        algo, n, r, p, salt_hex, hash_hex = stored.split("$")
    except ValueError:
        return False
    if algo != "scrypt":
        return False
    try:
        derived = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(bytes.fromhex(hash_hex)),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(derived.hex(), hash_hex)


def create_user(name, email, password):
    email = (email or "").strip().lower()
    name = (name or "").strip()
    if not name:
        raise ValueError("name_required")
    if "@" not in email or len(email) < 5:
        raise ValueError("email_invalid")
    if len(password or "") < 8:
        raise ValueError("password_short")
    try:
        return db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
            (name, email, hash_password(password)),
        )
    except mysql.connector.IntegrityError:
        raise ValueError("email_taken")


def authenticate(email, password):
    email = (email or "").strip().lower()
    if not email or not password:
        return None
    row = db.fetch_one(
        "SELECT user_id, name, email, password_hash FROM users WHERE email = %s", (email,)
    )
    if not row:
        return None
    if not verify_password(password, row["password_hash"]):
        return None
    return {"user_id": row["user_id"], "name": row["name"], "email": row["email"]}


def login_user(request, user):
    token = request.session.get(SESSION_TOKEN_KEY)
    request.session.clear()
    request.session[SESSION_USER_KEY] = user["user_id"]
    if token:
        request.session[SESSION_TOKEN_KEY] = token


def logout_user(request):
    token = request.session.get(SESSION_TOKEN_KEY)
    request.session.clear()
    if token:
        request.session[SESSION_TOKEN_KEY] = token


def current_user(request):
    uid = request.session.get(SESSION_USER_KEY)
    if not uid:
        return None
    row = db.fetch_one("SELECT user_id, name, email FROM users WHERE user_id = %s", (uid,))
    if not row:
        request.session.clear()
        return None
    return row


def redirect_to_login():
    return RedirectResponse("/login", status_code=303)


def redirect_home():
    return RedirectResponse("/", status_code=303)
