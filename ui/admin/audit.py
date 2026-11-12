"""Admin audit trail: every recorded investigation plus admin sign-in events."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from engine.explanation_engine import ExplanationEngine
from scenarios.sample_scenarios import SCENARIOS
from storage import (
    clear_investigations,
    list_investigations,
    load_investigation,
    load_record,
    log_admin_event,
    recent_admin_events,
)
from ui.shared.layout import severity_dataframe


def _investigations_tab() -> None:
    left, middle, right = st.columns(3)
    source_label = left.selectbox("Source", ["all", "manual", "scenario"], key="audit_source")
    scenario_options = ["all"] + [scenario.id for scenario in SCENARIOS]
    scenario_label = middle.selectbox("Scenario", scenario_options, key="audit_scenario")
    limit = right.slider("Maximum rows", 10, 200, 50, step=10, key="audit_limit")

    rows = list_investigations(
        limit=limit,
        source=None if source_label == "all" else source_label,
        scenario_id=None if scenario_label == "all" else scenario_label,
    )

    if not rows:
        st.info("No records match the current filters.")
        return

    st.dataframe(pd.DataFrame(rows), hide_index=True)

    st.divider()
    st.markdown("#### Inspect a record")
    identifiers = [row["id"] for row in rows]
    labels = {
        row["id"]: f"{row['id']} · {row['name']} · {row['created_at']}" for row in rows
    }
    chosen = st.selectbox(
        "Investigation", identifiers, format_func=lambda item: labels[item], key="audit_pick"
    )
    investigation = load_investigation(chosen)
    record = load_record(chosen)
    if investigation is None or record is None:
        st.error("The selected record could not be loaded.")
        return

    engine = ExplanationEngine()
    tabs = st.tabs(["Findings", "Observations", "Activations", "Actions"])
    with tabs[0]:
        if investigation.findings:
            st.dataframe(severity_dataframe(investigation.findings), hide_index=True)
        else:
            st.caption("No findings in this record.")
    with tabs[1]:
        observations = record.get("observations", {})
        st.dataframe(
            pd.DataFrame(
                [{"Fact": key, "Value": str(value)} for key, value in observations.items()]
            ),
            hide_index=True,
        )
    with tabs[2]:
        st.dataframe(
            pd.DataFrame(engine.activation_rows(investigation)), hide_index=True
        )
    with tabs[3]:
        if investigation.actions:
            st.dataframe(
                pd.DataFrame(engine.action_rows(investigation)), hide_index=True
            )
        else:
            st.caption("No actions in this record.")

    st.divider()
    left, right = st.columns(2)
    left.download_button(
        "Download record (JSON)",
        data=json.dumps(record, indent=2).encode("utf-8"),
        file_name=f"{investigation.id}.json",
        mime="application/json",
    )
    right.download_button(
        "Download summary (CSV)",
        data=pd.DataFrame(rows).to_csv(index=False).encode("utf-8"),
        file_name="ciares_investigations.csv",
        mime="text/csv",
    )

    st.divider()
    with st.expander("Danger zone"):
        confirmed = st.checkbox(
            "I understand this deletes every stored investigation.",
            key="audit_confirm_clear",
        )
        if st.button("Clear all records", disabled=not confirmed):
            clear_investigations()
            log_admin_event("clear", "all investigation records deleted")
            st.session_state["investigation"] = None
            st.rerun()


def _events_tab() -> None:
    st.caption("Admin sign-in, sign-out and destructive actions recorded by the portal.")
    events = recent_admin_events(limit=50)
    if events:
        st.dataframe(pd.DataFrame(events), hide_index=True)
    else:
        st.caption("No admin events recorded yet.")


def render() -> None:
    st.caption(
        "A record is written after every investigation and refreshed after execution. "
        "Records are session-independent while the container is awake."
    )
    tabs = st.tabs(["Investigations", "Admin events"])
    with tabs[0]:
        _investigations_tab()
    with tabs[1]:
        _events_tab()
