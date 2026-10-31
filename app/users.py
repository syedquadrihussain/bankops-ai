import hashlib
import hmac
import secrets
import sqlite3
from contextlib import contextmanager

from app import review_store

VALID_ROLES = ("analyst", "reviewer")
MIN_PASSWORD_LENGTH = 8
_N, _R, _P = 2**14, 8, 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_N, r=_R, p=_P
    )
    return f"scrypt${_N}${_R}${_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt_hex, digest_hex = stored.split("$")
        if scheme != "scrypt":
            return False
        digest = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
        )
        expected = bytes.fromhex(digest_hex)
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest, expected)


# Used so a missing user takes about as long as a wrong password.
_DUMMY_HASH = hash_password("not-a-real-password")


@contextmanager
def _connection():
    conn = sqlite3.connect(review_store._db_path())
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(SCHEMA)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def create_user(username: str, password: str, role: str) -> dict:
    username = username.strip().lower()
    if not username:
        raise ValueError("Username must not be empty.")
    if role not in VALID_ROLES:
        raise ValueError("Role must be one of: " + ", ".join(VALID_ROLES))
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
        )
    try:
        with _connection() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash, role, created_at) "
                "VALUES (?, ?, ?, ?)",
                (username, hash_password(password), role, review_store.utc_now()),
            )
    except sqlite3.IntegrityError:
        raise ValueError("Username already exists.")
    return {"username": username, "role": role}


def authenticate(username: str, password: str):
    """Return {"username", "role"} if the password is right, else None."""
    username = username.strip().lower()
    with _connection() as conn:
        row = conn.execute(
            "SELECT username, password_hash, role FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    if row is None:
        verify_password(password, _DUMMY_HASH)
        return None
    if verify_password(password, row["password_hash"]):
        return {"username": row["username"], "role": row["role"]}
    return None
