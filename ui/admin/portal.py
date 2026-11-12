"""The hidden admin portal: sign-in gate followed by the expert-system internals."""

from __future__ import annotations

import streamlit as st

from ui.admin import audit, dashboard, decision, inference, knowledge, system_map
from ui.shared.auth import account_bar, require_admin
from ui.shared.layout import page_title

TABS = (
    "Dashboard",
    "Knowledge base",
    "Inference engine",
    "Decision engine",
    "Audit",
    "System map",
)


def render() -> None:
    if not require_admin():
        st.stop()

    page_title(
        "Administration",
        "The internal view of CIARES: the knowledge base, the inference engine, the "
        "decision engine and the audit trail. The public portal never exposes this.",
    )
    account_bar()
    st.divider()

    tabs = st.tabs(list(TABS))
    renderers = (
        dashboard.render,
        knowledge.render,
        inference.render,
        decision.render,
        audit.render,
        system_map.render,
    )
    for tab, renderer in zip(tabs, renderers):
        with tab:
            renderer()
