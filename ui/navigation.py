"""In-app navigation helper (kept separate to avoid a page-registry cycle)."""

from __future__ import annotations

import streamlit as st


def go(page: str) -> None:
    """Switch to a registered page by name."""
    from ui.nav import get_pages

    st.switch_page(get_pages()[page])
