"""
Admin authentication gate for the hidden ``/admin`` route.

The public portal has no authentication by design: anyone with the link can
investigate an incident. The admin portal - which exposes the knowledge base,
the inference engine and the decision engine - is reachable only by typing the
URL and signing in.

This is a session-level gate, not a user database. It exists so the internals
are not part of the public surface, and it is described honestly as a
demonstration control.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st

from storage import log_admin_event

from .passwords import verify_credentials

MAX_ATTEMPTS = 5
DEFAULT_EMAIL = "admin@ciares.local"


def _auth_section() -> dict[str, Any]:
    try:
        section = st.secrets.get("auth", {})
    except Exception:  # no secrets file configured
        return {}
    return dict(section) if section else {}


def configured() -> bool:
    section = _auth_section()
    return bool(section.get("admin_password_hash") or section.get("admin_password"))


def signed_in() -> bool:
    return bool(st.session_state.get("admin_ok"))


def _attempts() -> int:
    return int(st.session_state.get("admin_attempts", 0))


def _register_failure(email: str) -> None:
    st.session_state["admin_attempts"] = _attempts() + 1
    log_admin_event("login_fail", email or "(no email)")
    if _attempts() >= MAX_ATTEMPTS:
        st.error(
            "Too many failed attempts. The sign-in form is locked for this session; "
            "reload the page to try again."
        )


def _register_success(email: str) -> None:
    st.session_state["admin_ok"] = True
    st.session_state["admin_email"] = email
    st.session_state["admin_since"] = datetime.now().isoformat(timespec="seconds")
    st.session_state["admin_attempts"] = 0
    log_admin_event("login_ok", email)


def sign_out() -> None:
    email = st.session_state.get("admin_email", "")
    st.session_state["admin_ok"] = False
    st.session_state.pop("admin_email", None)
    st.session_state.pop("admin_since", None)
    log_admin_event("logout", email)


def _login_form() -> None:
    st.markdown("### Administrator sign-in")
    st.caption(
        "This area exposes the knowledge base, the inference engine and the "
        "decision engine. It is not part of the public investigation portal."
    )

    if not configured():
        st.warning(
            "No admin credential is configured. Add an [auth] section to "
            ".streamlit/secrets.toml (or the Streamlit Cloud app secrets)."
        )
        return

    if _attempts() >= MAX_ATTEMPTS:
        st.error("Sign-in is locked for this session after repeated failures.")
        return

    section = _auth_section()
    expected_email = str(section.get("admin_email", DEFAULT_EMAIL))
    stored_hash = section.get("admin_password_hash")
    stored_password = section.get("admin_password")

    with st.form("admin_login_form", clear_on_submit=False):
        email = st.text_input("Email", placeholder=expected_email, autocomplete="username")
        password = st.text_input(
            "Password", type="password", autocomplete="current-password"
        )
        submitted = st.form_submit_button("Sign in", type="primary")

    if not submitted:
        return

    if verify_credentials(
        email,
        password,
        stored_email=expected_email,
        stored_hash=stored_hash,
        stored_password=stored_password,
    ):
        _register_success(email.strip().lower())
        st.rerun()
    else:
        _register_failure(email.strip())
        st.error("Invalid credentials.")


def require_admin() -> bool:
    """Render the gate when necessary; return True only for a signed-in admin."""
    if signed_in():
        return True
    _login_form()
    return False


def account_bar() -> None:
    """Small signed-in strip with a sign-out control."""
    email = st.session_state.get("admin_email", "administrator")
    since = st.session_state.get("admin_since", "")
    left, right = st.columns([3, 1])
    left.caption(f"Signed in as **{email}**" + (f" · since {since}" if since else ""))
    if right.button("Sign out", use_container_width=True):
        sign_out()
        st.rerun()
