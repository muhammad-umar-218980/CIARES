"""Shared admin helpers: investigation selection from the audit store."""

from __future__ import annotations

from typing import Any

import streamlit as st

from engine.models import Investigation
from storage import list_investigations, load_investigation, load_record


def select_investigation(
    key: str,
) -> tuple[dict[str, Any] | None, Investigation | None, dict[str, Any] | None]:
    """Pick a stored investigation and return (summary row, object, raw payload)."""
    rows = list_investigations(limit=200)
    if not rows:
        st.info(
            "No investigations recorded yet. Run one from the public portal and it "
            "will appear here."
        )
        return None, None, None

    identifiers = [row["id"] for row in rows]
    labels = {
        row["id"]: (
            f"{row['id']} · {row['name']} · {row['created_at']} · "
            f"{row['findings']} finding(s)"
        )
        for row in rows
    }
    chosen = st.selectbox(
        "Investigation", identifiers, format_func=lambda item: labels[item], key=key
    )
    row = next(item for item in rows if item["id"] == chosen)
    return row, load_investigation(chosen), load_record(chosen)
