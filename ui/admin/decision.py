"""Admin decision view: how findings become validated, ordered responses."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from engine.decision_engine import ACTION_LIBRARY, DecisionEngine
from engine.explanation_engine import ExplanationEngine
from engine.models import ResponseAction, Severity
from simulation.environment import SimulatedEnvironment
from ui.admin.common import select_investigation
from ui.shared.layout import page_title

DECISION_RULES = (
    "An action is proposed only when the rule behind a finding recommends it.",
    "The target identifier must exist in the simulated environment.",
    "The target must be in a state where the action makes sense.",
    "Duplicate actions against the same target are collapsed into one.",
    "Recovery is deferred while a containment action targets the same entity.",
    "Actions are ordered by response phase, then by declared priority.",
)


def _catalogue() -> None:
    st.markdown("#### Action catalogue")
    st.caption(
        "Every response the simulation can execute, with the phase, urgency and target "
        "state that make it applicable."
    )
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Action key": spec.key,
                    "Label": spec.label,
                    "Phase": spec.phase.value,
                    "Priority": spec.priority,
                    "Target": spec.target_type,
                    "Requires": spec.required_field,
                    "Valid states": ", ".join(sorted(spec.required_values))
                    if spec.required_values
                    else "any",
                }
                for spec in sorted(
                    ACTION_LIBRARY.values(), key=lambda item: (item.phase.order, item.priority)
                )
            ]
        ),
        hide_index=True,
    )


def _validation_lab() -> None:
    st.markdown("#### Target validation lab")
    st.caption(
        "The Decision Engine rejects a response whose target does not exist or is in "
        "the wrong state. Try an identifier that is not in the inventory."
    )

    environment = SimulatedEnvironment()
    action_key = st.selectbox(
        "Action to validate", sorted(ACTION_LIBRARY), key="admin_validation_action"
    )
    spec = ACTION_LIBRARY[action_key]

    if spec.target_type == "incident":
        st.info("This action targets the investigation itself, so no identifier is required.")
        return

    known = sorted(environment.entities.get(spec.target_type, {}))
    st.caption(
        f"Targets a **{spec.target_type}**. Inventory: "
        + (", ".join(known) if known else "(empty)")
    )

    target_id = st.text_input(
        "Target identifier",
        value="USER-999" if spec.target_type == "account" else (known[0] if known else ""),
        key="admin_validation_target",
    )

    if st.button("Validate target", type="primary"):
        engine = DecisionEngine(environment)
        action = ResponseAction(
            action=spec.key,
            label=spec.label,
            phase=spec.phase,
            priority=spec.priority,
            target_type=spec.target_type,
            target_id=target_id.strip(),
            finding_key="validation-lab",
            finding_label="Target validation lab",
            finding_severity=Severity.LOW,
            reason="Manual validation request from the admin portal",
        )
        engine.validate_target(action, spec)

        if action.executable:
            st.success(
                f"Target {target_id} is valid. The action would be executable on "
                f"{spec.target_type} {target_id}."
            )
        else:
            st.error(action.blocked_reason)


def render() -> None:
    page_title(
        "Decision engine",
        "The inference engine answers what is happening; this layer decides what should "
        "be done about it.",
    )

    st.markdown("#### Decision rules applied")
    for index, rule in enumerate(DECISION_RULES, start=1):
        st.markdown(f"{index}. {rule}")

    st.divider()
    _row, investigation, _record = select_investigation("admin_decision")
    if investigation is None:
        return

    engine = ExplanationEngine()
    st.markdown("#### Proposed actions")
    if investigation.actions:
        st.dataframe(
            pd.DataFrame(engine.action_rows(investigation))[
                [
                    "ID",
                    "Phase",
                    "Priority",
                    "Action",
                    "Target",
                    "Finding",
                    "Executable",
                    "Status",
                    "Blocked reason",
                ]
            ],
            hide_index=True,
        )
        st.caption(
            "Ordering follows containment → eradication → recovery → escalation. "
            "A deferred recovery action is marked Skipped with its reason."
        )
    else:
        st.caption("No action was proposed for this investigation.")

    st.divider()
    _catalogue()
    st.divider()
    _validation_lab()
