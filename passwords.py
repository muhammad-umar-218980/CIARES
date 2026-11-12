"""
Password hashing and credential checks (no Streamlit dependency).

The admin credential is not stored in source control. A PBKDF2-SHA256 hash is
kept in ``.streamlit/secrets.toml`` (locally) and in the Streamlit Cloud app
secrets. Verification is constant-time.

This is a demonstration gate for a single administrator, not a multi-user
identity provider.
"""

from __future__ import annotations

import hashlib
import hmac
import os

ALGORITHM = "pbkdf2_sha256"
DEFAULT_ITERATIONS = 260_000


def hash_password(
    password: str,
    *,
    iterations: int = DEFAULT_ITERATIONS,
    salt: bytes | None = None,
) -> str:
    """Return ``pbkdf2_sha256$iterations$salt_hex$hash_hex``."""
    if not password:
        raise ValueError("password must not be empty")
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{ALGORITHM}${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Constant-time verification of a password against a stored hash."""
    if not password or not stored:
        return False
    try:
        algorithm, iterations, salt_hex, digest_hex = stored.split("$")
        if algorithm != ALGORITHM:
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, int(iterations)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(candidate, expected)


def verify_credentials(
    email: str,
    password: str,
    *,
    stored_email: str,
    stored_hash: str | None = None,
    stored_password: str | None = None,
) -> bool:
    """
    Check an email/password pair.

    ``stored_hash`` takes precedence. ``stored_password`` exists only as a
    convenience fallback for local experimentation and is documented as less
    safe. Both comparisons are constant-time and both are always evaluated so
    timing does not reveal which field was wrong.
    """
    email_ok = hmac.compare_digest(
        (email or "").strip().lower(), (stored_email or "").strip().lower()
    )
    if stored_hash:
        password_ok = verify_password(password, stored_hash)
    elif stored_password:
        password_ok = hmac.compare_digest(password or "", stored_password)
    else:
        password_ok = False
    return email_ok and password_ok
