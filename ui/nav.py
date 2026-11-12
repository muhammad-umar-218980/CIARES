"""Page registry shared by the entry point and by in-app navigation."""

from __future__ import annotations

import streamlit as st

from ui.admin import portal
from ui.user import home, investigate, results, scenarios

_PAGES: dict[str, st.Page] | None = None

def get_pages() -> dict[str, st.Page]:
    """Build (once) the st.Page objects used by st.navigation and st.switch_page."""
    global _PAGES
    if _PAGES is None:
        _PAGES = {
            "home": st.Page(
                home.render,
                title="Home",
                url_path="home",
                icon="🏠",
                default=True,
            ),
            "investigate": st.Page(
                investigate.render,
                title="Investigate",
                url_path="investigate",
                icon="🔎",
            ),
            "scenarios": st.Page(
                scenarios.render,
                title="Scenarios",
                url_path="scenarios",
                icon="🧪",
            ),
            "results": st.Page(
                results.render,
                title="Results",
                url_path="results",
                icon="📋",
            ),
            # Hidden via CSS in the sidebar; reachable only by typing /admin.
            "admin": st.Page(
                portal.render,
                title="Admin portal",
                url_path="admin",
                icon="🔐",
            ),
        }
    return _PAGES
