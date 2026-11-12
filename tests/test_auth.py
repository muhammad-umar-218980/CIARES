"""Password hashing and credential verification (no Streamlit runtime needed)."""

from __future__ import annotations

from ui.shared.passwords import hash_password, verify_credentials, verify_password


def test_hash_verifies_the_original_password():
    stored = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", stored)


def test_wrong_password_is_rejected():
    stored = hash_password("correct horse battery staple")
    assert not verify_password("Correct horse battery staple", stored)
    assert not verify_password("", stored)


def test_hash_is_salted():
    first = hash_password("same password")
    second = hash_password("same password")
    assert first != second
    assert verify_password("same password", first)
    assert verify_password("same password", second)


def test_malformed_hash_is_rejected():
    assert not verify_password("anything", "not-a-hash")
    assert not verify_password("anything", "bcrypt$1$aa$bb")


def test_credentials_match_email_case_insensitively():
    stored = hash_password("secret-value")
    assert verify_credentials(
        "Admin@CIARES.local",
        "secret-value",
        stored_email="admin@ciares.local",
        stored_hash=stored,
    )


def test_credentials_reject_wrong_email_or_password():
    stored = hash_password("secret-value")
    assert not verify_credentials(
        "someone@else.local",
        "secret-value",
        stored_email="admin@ciares.local",
        stored_hash=stored,
    )
    assert not verify_credentials(
        "admin@ciares.local",
        "wrong-value",
        stored_email="admin@ciares.local",
        stored_hash=stored,
    )


def test_plaintext_fallback_still_works():
    assert verify_credentials(
        "admin@ciares.local",
        "legacy",
        stored_email="admin@ciares.local",
        stored_password="legacy",
    )
