"""Results: the diagnosis, the reasoning behind it, and the approved response."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from engine.explanation_engine import ExplanationEngine
from ui.navigation import go
from ui.shared.investigation import current, execute_approved
from ui.shared.layout import (
    page_title,
    severity_badge,
    severity_chart,
    severity_counts,
    severity_dataframe,
    simulation_disclaimer,
)


def _observed(value, known: bool) -> str:
    if not known:
        return "Unknown"
    if isinstance(value, bool):
        return "True" if value else "False"
    return str(value)


def _why_expanders(investigation) -> None:
    """Show, per finding, the rules and satisfied conditions that produced it."""
    for finding in investigation.findings:
        with st.expander(f"Why this finding? — {finding.label}"):
            st.caption(
                f"{finding.module} · {finding.severity.value} · "
                f"rules: {', '.join(finding.rule_ids)}"
            )
            activations = [
                activation
                for activation in investigation.activations
                if activation.rule.id in finding.rule_ids
            ]
            if not activations:
                st.caption("The supporting rule activation is not available for this record.")
                continue
            for activation in activations:
                st.markdown(f"**{activation.rule.id} · {activation.rule.name}**")
                st.caption(
                    f"Module: {activation.rule.module} · "
                    f"Severity: {activation.rule.severity.value} · "
                    f"Source: {activation.rule.source}"
                )
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "Condition": evaluation.condition.describe(),
                                "Observed": _observed(evaluation.observed, evaluation.known),
                                "Status": evaluation.status,
                            }
                            for evaluation in activation.evaluations
                        ]
                    ),
                    hide_index=True,
                )
                st.markdown(
                    f"**THEN** `{activation.conclusion_key}` = True "
                    f"({activation.conclusion_label})"
                )


def render() -> None:
    page_title(
        "Investigation results",
        "The diagnosis, the reasoning behind each finding, and the response awaiting "
        "your approval.",
    )

    investigation = current()
    if investigation is None:
        st.info(
            "No investigation loaded. Run a manual investigation or load a scenario "
            "first.",
            icon="🧭",
        )
        if st.button("Start an investigation", type="primary"):
            go("investigate")
        return

    counts = severity_counts(investigation.findings)
    st.markdown(
        f"**{investigation.id}** · {investigation.name} · "
        f"{investigation.started_at}"
        + (f" · scenario {investigation.scenario_id}" if investigation.scenario_id else "")
    )

    left, right = st.columns([1, 1.2])
    with left:
        st.markdown("#### Threat summary")
        st.markdown(f"**{severity_badge(investigation.findings)}**")
        top = st.columns(2)
        top[0].metric("Findings", len(investigation.findings))
        top[1].metric("Critical", counts["Critical"])
        bottom = st.columns(2)
        bottom[0].metric("Proposed actions", len(investigation.actions))
        bottom[1].metric(
            "Executable", sum(1 for action in investigation.actions if action.executable)
        )
    with right:
        st.markdown("#### Findings by severity")
        severity_chart(investigation.findings)

    st.divider()
    st.markdown("#### Diagnosis")
    if investigation.findings:
        st.dataframe(severity_dataframe(investigation.findings), hide_index=True)
        _why_expanders(investigation)
    else:
        st.info(
            "No findings were derived, therefore no response is justified.",
            icon="✅",
        )
        return

    st.divider()
    st.markdown("#### Proposed responses")
    if not investigation.actions:
        st.caption(
            "No actionable finding. Diagnostic rules produce findings; only findings "
            "whose rule recommends a response create an action."
        )
        simulation_disclaimer()
        return

    engine = ExplanationEngine()
    st.dataframe(
        pd.DataFrame(engine.action_rows(investigation))[
            ["ID", "Phase", "Action", "Target", "Finding", "Executable", "Status"]
        ],
        hide_index=True,
    )

    proposed = [
        action
        for action in investigation.actions
        if action.executable and action.status == "Proposed"
    ]
    deferred = [action for action in investigation.actions if not action.executable]

    st.markdown("##### Why these actions")
    for action in investigation.actions:
        st.markdown(
            f"- **{action.action_id} {action.label}** → {action.target_type}:{action.target} — "
            f"{action.reason}"
        )

    if deferred:
        with st.expander(f"Blocked or deferred actions ({len(deferred)})"):
            for action in deferred:
                st.markdown(
                    f"- **{action.action_id} {action.label}** — {action.blocked_reason}"
                )

    st.markdown("##### Decision support")
    if not proposed:
        st.success("No further executable actions. Review the results below.")
    else:
        labels = {
            action.action_id: (
                f"{action.action_id} · {action.label} → "
                f"{action.target_type}:{action.target}"
            )
            for action in proposed
        }
        approved = st.multiselect(
            "Approve simulated actions to execute",
            options=list(labels),
            default=list(labels),
            format_func=lambda action_id: labels[action_id],
        )
        simulation_disclaimer()
        if st.button("Execute approved actions", type="primary", disabled=not approved):
            results = execute_approved(investigation, approved)
            succeeded = sum(1 for result in results if result.success)
            st.toast(f"{succeeded}/{len(results)} action(s) executed.")
            st.rerun()

    executed = [
        action for action in investigation.actions if action.execution is not None
    ]
    if executed:
        st.markdown("#### Execution results")
        for action in executed:
            st.markdown(engine.action_markdown(action))

        environment = investigation.environment
        if environment is not None:
            st.markdown("#### Simulated environment after execution")
            st.dataframe(pd.DataFrame(environment.snapshot()), hide_index=True)

    simulation_disclaimer()
