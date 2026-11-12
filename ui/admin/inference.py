"""Admin inference view: activation order, justification and working memory."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from engine.explanation_engine import ExplanationEngine
from ui.admin.common import select_investigation


def _working_memory(record: dict) -> None:
    observations = record.get("observations", {})
    if observations:
        st.markdown("#### Observations")
        st.dataframe(
            pd.DataFrame(
                [
                    {"Fact": key, "Value": str(value), "Source": "Observation"}
                    for key, value in observations.items()
                ]
            ),
            hide_index=True,
        )
    else:
        st.caption("No observations in this record.")

    derived = record.get("derived", [])
    st.markdown("#### Derived conclusions (with provenance)")
    if derived:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Fact": item["key"],
                        "Value": str(item.get("value", "True")),
                        "Derived by": item.get("rule_id") or "",
                        "Supporting facts": ", ".join(
                            f"{key}={value}" for key, value in item.get("supporting", [])
                        ),
                    }
                    for item in derived
                ]
            ),
            hide_index=True,
        )
    else:
        st.caption(
            "No derived-fact provenance stored for this record. The activation table "
            "still shows which rule produced each conclusion."
        )


def render() -> None:
    st.caption(
        "Forward chaining fires one rule per cycle and records the real reasoning "
        "order. Activation keys stop the same rule firing twice on identical evidence."
    )

    _row, investigation, record = select_investigation("admin_inference")
    if investigation is None or record is None:
        return

    engine = ExplanationEngine()
    st.markdown(
        f"**{investigation.id}** · {investigation.name} · "
        f"{len(investigation.activations)} activation(s) · "
        f"{investigation.terminated_reason}"
    )

    tabs = st.tabs(
        ["Activation sequence", "Justification", "Working memory", "Reasoning log"]
    )

    with tabs[0]:
        if investigation.activations:
            st.dataframe(
                pd.DataFrame(engine.activation_rows(investigation)),
                hide_index=True,
                column_config={"#": st.column_config.NumberColumn(width="small")},
            )
        else:
            st.info("No rule activated for this investigation.")

    with tabs[1]:
        if not investigation.activations:
            st.info("Nothing to justify yet.")
        else:
            identifiers = [activation.rule.id for activation in investigation.activations]
            chosen = st.selectbox("Rule activation", identifiers, key="admin_justify_rule")
            activation = next(
                item for item in investigation.activations if item.rule.id == chosen
            )
            st.markdown(engine.justification_markdown(activation))
            st.dataframe(
                pd.DataFrame(engine.justification(activation)["conditions"]),
                hide_index=True,
            )

    with tabs[2]:
        _working_memory(record)

    with tabs[3]:
        st.dataframe(
            pd.DataFrame(engine.trace_rows(investigation)),
            hide_index=True,
            column_config={
                "Step": st.column_config.NumberColumn(width="small"),
                "Event": st.column_config.TextColumn(width="small"),
                "Detail": st.column_config.TextColumn(width="large"),
            },
        )

    st.divider()
    st.download_button(
        "Download investigation report (Markdown)",
        data=engine.markdown_report(investigation).encode("utf-8"),
        file_name=f"{investigation.id}.md",
        mime="text/markdown",
    )
