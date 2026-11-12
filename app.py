"""
CIARES - Cybersecurity Incident Analysis and Response Expert System.

This file is the entry point only: it configures the page, registers the routes
and hands control to ``st.navigation``. No cybersecurity knowledge and no
inference logic live here.

Routes
------
/               public home
/investigate    manual investigation form
/scenarios      six predefined investigations
/results        diagnosis, reasoning and approved response
/admin          hidden administration portal (email + password)
"""

from __future__ import annotations

import streamlit as st

from config import APP_NAME
from ui.nav import get_pages
from ui.shared.investigation import init_state
from ui.shared.layout import apply_theme, footer


def main() -> None:
    st.set_page_config(
        page_title=f"{APP_NAME} · Expert System",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_theme()
    init_state()

    navigation = st.navigation(list(get_pages().values()))
    navigation.run()
    footer()


main()
