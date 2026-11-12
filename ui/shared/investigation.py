"""Session state and the single investigation entry point used by the UI."""

from __future__ import annotations

from typing import Any

import streamlit as st

from engine.entities import default_entities
from engine.models import Investigation
from engine.pipeline import run_investigation
from simulation import execute
from storage import init_db, save_investigation


def init_state() -> None:
    init_db()
    st.session_state.setdefault("investigation", None)
    st.session_state.setdefault("admin_ok", False)
    st.session_state.setdefault("admin_attempts", 0)


def current() -> Investigation | None:
    investigation = st.session_state.get("investigation")
    return investigation if isinstance(investigation, Investigation) else None


def launch(
    observations: dict[str, Any],
    name: str,
    entities: dict[str, str] | None = None,
    scenario_id: str | None = None,
) -> Investigation:
    """
    Run the pipeline and record the investigation.

    Manual investigations receive one valid target per entity type from the
    simulated inventory, so the analyst never types identifiers. Scenarios keep
    the entity map they declare.
    """
    investigation = run_investigation(
        observations=observations,
        entities=entities or default_entities(),
        name=name,
        scenario_id=scenario_id,
    )
    st.session_state.investigation = investigation
    save_investigation(investigation)
    return investigation


def execute_approved(investigation: Investigation, action_ids: list[str]) -> list[Any]:
    """Execute the approved subset and persist the updated record."""
    environment = investigation.environment
    results = []
    for action in investigation.actions:
        if action.action_id in action_ids and action.status == "Proposed":
            results.append(execute(environment, action))
    save_investigation(investigation)
    return results


def persist(investigation: Investigation) -> None:
    save_investigation(investigation)
