"""Admin dashboard: knowledge-base health and cross-investigation statistics."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from knowledge_base.knowledge_acquisition import validate_catalogue
from knowledge_base.rule_registry import ALL_RULES, MODULES, module_summary
from simulation.environment import SimulatedEnvironment
from storage import recent_admin_events, stats
from ui.shared.layout import metric_row


def render() -> None:
    report = validate_catalogue(ALL_RULES)
    summary = stats()

    metric_row(
        [
            ("Investigations", summary["investigations"], "Records in the SQLite store"),
            ("Findings", summary["findings"], "Total findings across all runs"),
            ("Critical", summary["critical"], "Critical findings"),
            ("Actions executed", summary["executed"], "Simulated executions"),
            ("Rules", len(ALL_RULES), "Registered IF-THEN rules"),
            ("Conditions", report.condition_count, "Logical conditions in the knowledge base"),
        ]
    )

    st.divider()
    left, right = st.columns(2)
    with left:
        st.markdown("#### Findings by severity")
        if summary["findings"]:
            st.bar_chart(
                pd.DataFrame(
                    {
                        "Severity": ["Critical", "High", "Medium", "Low"],
                        "Findings": [
                            summary["critical"],
                            summary["high"],
                            summary["medium"],
                            summary["low"],
                        ],
                    }
                ),
                x="Severity",
                y="Findings",
                height=240,
            )
        else:
            st.caption("No findings recorded yet.")

    with right:
        st.markdown("#### Findings by module")
        modules = summary.get("by_module", {})
        if modules:
            frame = pd.DataFrame(
                sorted(modules.items(), key=lambda item: -item[1]),
                columns=["Module", "Findings"],
            )
            st.bar_chart(frame, x="Module", y="Findings", height=240)
        else:
            st.caption("No findings recorded yet.")

    st.divider()
    left, right = st.columns([1.2, 1])
    with left:
        st.markdown("#### Knowledge base")
        st.dataframe(
            pd.DataFrame(module_summary()).rename(
                columns={"module": "Module", "rules": "Rules", "conditions": "Conditions"}
            ),
            hide_index=True,
        )
        status = "✅ catalogue valid" if report.ok else f"⚠️ {len(report.errors)} error(s)"
        st.caption(f"{report.summary()} · {status}")
        if report.errors:
            st.error("\n".join(f"- {error}" for error in report.errors))

    with right:
        st.markdown("#### Recent admin activity")
        events = recent_admin_events(limit=8)
        if events:
            st.dataframe(pd.DataFrame(events), hide_index=True)
        else:
            st.caption("No admin events recorded.")

    st.divider()
    st.markdown("#### Simulated environment inventory")
    st.caption(
        "The fixed world that response actions operate on. Targets are validated "
        "against this inventory before an action becomes executable."
    )
    st.dataframe(pd.DataFrame(SimulatedEnvironment().snapshot()), hide_index=True)

    st.caption(
        "Storage note: records live in data/ciares.db. On Streamlit Community Cloud "
        "the filesystem is ephemeral, so records reset after a redeploy or a long sleep."
    )
