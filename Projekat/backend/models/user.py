import hashlib
import hmac
import secrets

from database.db import get_connection


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        200_000,
    ).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    salt, digest = stored_hash.split("$", 1)
    candidate = hash_password(password, salt).split("$", 1)[1]
    return hmac.compare_digest(candidate, digest)


def create_user(username: str, password: str):
    api_token = secrets.token_urlsafe(32)
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash, api_token) VALUES (?, ?, ?)",
            (username, hash_password(password), api_token),
        )
        return {"id": cursor.lastrowid, "username": username, "api_token": api_token}


def authenticate_user(username: str, password: str):
    with get_connection() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ).fetchone()

    if not user or not verify_password(password, user["password_hash"]):
        return None

    return {"id": user["id"], "username": user["username"], "api_token": user["api_token"]}


def get_user_by_token(token: str):
    with get_connection() as conn:
        user = conn.execute(
            "SELECT id, username FROM users WHERE api_token = ?",
            (token,),
        ).fetchone()

    return dict(user) if user else None
