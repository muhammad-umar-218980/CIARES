"""Manual investigation form. Entity targets are assigned automatically."""

from __future__ import annotations

from typing import Any

import streamlit as st

from ui.navigation import go
from ui.schema import OBSERVATION_SCHEMA, TRI_OPTIONS, TRI_VALUES
from ui.shared.investigation import current, launch
from ui.shared.layout import page_title, severity_dataframe, severity_counts


def _field(container, key: str, label: str, kind: str) -> None:
    if kind == "number":
        container.number_input(label, min_value=0, step=1, value=0, key=f"obs_{key}")
    elif kind == "tri":
        container.selectbox(label, TRI_OPTIONS, index=0, key=f"obs_{key}")
    else:
        container.text_input(label, key=f"obs_{key}")


def _collect() -> dict[str, Any]:
    observations: dict[str, Any] = {}
    for fields in OBSERVATION_SCHEMA.values():
        for key, _label, kind in fields:
            raw = st.session_state.get(f"obs_{key}")
            if kind == "number":
                observations[key] = int(raw or 0)
            elif kind == "tri":
                value = TRI_VALUES.get(str(raw))
                if value is not None:
                    observations[key] = value
            elif raw:
                observations[key] = raw
    return observations


def _show_result(investigation) -> None:
    counts = severity_counts(investigation.findings)
    st.success(
        f"{investigation.id}: {len(investigation.activations)} rule activation(s), "
        f"{len(investigation.findings)} finding(s), "
        f"{len(investigation.actions)} proposed action(s)."
    )

    if not investigation.findings:
        st.info(
            "No rule fired for these observations. That is a valid result: CIARES "
            "does not invent findings from missing evidence.",
            icon="✅",
        )
        return

    columns = st.columns(4)
    columns[0].metric("Findings", len(investigation.findings))
    columns[1].metric("Critical", counts["Critical"])
    columns[2].metric("High", counts["High"])
    columns[3].metric("Proposed actions", len(investigation.actions))

    st.dataframe(severity_dataframe(investigation.findings), hide_index=True)
    if st.button("Open full results", type="primary"):
        go("results")


def render() -> None:
    page_title(
        "Investigate an incident",
        "Enter what was observed. Boolean fields have three states: True (confirmed), "
        "False (explicitly absent) and Unknown (not provided). Unknown never satisfies "
        "a rule.",
    )

    with st.form("investigation_form", clear_on_submit=False):
        name = st.text_input(
            "Investigation name", placeholder="e.g. Suspicious administrator activity"
        )
        st.caption(
            "Response targets are assigned automatically from the simulated inventory, "
            "so there are no identifiers to type."
        )

        for group, fields in OBSERVATION_SCHEMA.items():
            with st.expander(group, expanded=group.startswith("Authentication")):
                columns = st.columns(2)
                for index, (key, label, kind) in enumerate(fields):
                    _field(columns[index % 2], key, label, kind)

        submitted = st.form_submit_button("Run investigation", type="primary")

    if submitted:
        observations = _collect()
        if not observations:
            st.warning(
                "No observations supplied. Every condition is Unknown, so no rule can fire."
            )
            return
        investigation = launch(observations, name or "Manual investigation")
        _show_result(investigation)
        return

    investigation = current()
    if investigation is not None and investigation.scenario_id is None:
        st.divider()
        st.markdown("#### Last result")
        _show_result(investigation)
