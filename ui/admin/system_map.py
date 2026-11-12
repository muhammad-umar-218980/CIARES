"""Admin system map: what each module does and what breaks if it is removed."""

from __future__ import annotations

import streamlit as st

from config import PROJECT_ROOT

DOCUMENT = PROJECT_ROOT / "docs" / "system_map.md"


def render() -> None:
    st.caption(
        "A reading guide to the codebase, written for the question 'what does this "
        "function do?' and 'what happens if I delete it?'."
    )
    if not DOCUMENT.exists():
        st.warning(f"System map not found at {DOCUMENT}.")
        return
    st.markdown(DOCUMENT.read_text(encoding="utf-8"))
