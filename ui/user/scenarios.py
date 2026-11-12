"""Scenario laboratory: six predefined investigations using the same pipeline."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from scenarios.sample_scenarios import SCENARIOS, get_scenario
from ui.navigation import go
from ui.shared.investigation import current, launch
from ui.shared.layout import page_title, severity_dataframe


def render() -> None:
    page_title(
        "Scenario laboratory",
        "A scenario supplies observations and entity identifiers only. The diagnosis, "
        "the responses and the execution all come from the same engine used for manual "
        "investigations.",
    )

    scenario_ids = [scenario.id for scenario in SCENARIOS]
    selected_id = st.selectbox(
        "Scenario",
        scenario_ids,
        format_func=lambda sid: f"{sid} · {get_scenario(sid).name}",
    )
    scenario = get_scenario(selected_id)

    st.markdown(f"**{scenario.name}**")
    st.write(scenario.summary)

    left, right = st.columns([1.4, 1])
    with left:
        st.markdown("#### Observations")
        st.dataframe(
            pd.DataFrame(
                [
                    {"Fact": key, "Value": str(value)}
                    for key, value in scenario.observations.items()
                ]
            ),
            hide_index=True,
        )
    with right:
        st.markdown("#### Entities")
        if scenario.entities:
            st.dataframe(
                pd.DataFrame(
                    [{"Entity": key, "ID": value} for key, value in scenario.entities.items()]
                ),
                hide_index=True,
            )
        else:
            st.caption("No entity IDs supplied.")
        with st.expander("Verification chain (used by the test suite)"):
            st.caption(
                "The scenario supplies observations only. Every finding below must be "
                "derived by the inference engine; the test suite asserts it."
            )
            for key in scenario.expected_findings:
                st.markdown(f"- `{key}`")

    if st.button("Run scenario", type="primary"):
        investigation = launch(
            scenario.observations,
            scenario.name,
            entities=scenario.entities,
            scenario_id=scenario.id,
        )
        st.success(
            f"{investigation.id}: {len(investigation.activations)} activation(s), "
            f"{len(investigation.findings)} finding(s)."
        )

    investigation = current()
    if investigation and investigation.scenario_id == scenario.id:
        st.markdown("#### Result of the last run")
        if investigation.findings:
            st.dataframe(severity_dataframe(investigation.findings), hide_index=True)
        else:
            st.warning("No finding was derived for this scenario, which would be a regression.")

        missing = [
            key
            for key in scenario.expected_findings
            if key not in {finding.key for finding in investigation.findings}
        ]
        if missing:
            st.error(
                "Expected but not derived (regression): "
                + ", ".join(f"`{key}`" for key in missing)
            )
        else:
            st.caption(
                f"All {len(scenario.expected_findings)} expected findings were derived."
            )

        if st.button("Open full results", type="primary"):
            go("results")
