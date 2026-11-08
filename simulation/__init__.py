"""
Simulated execution layer.

``execute`` is the only entry point the UI and the Decision Engine need: it
routes a ResponseAction to the right action module, applies the state change to
the simulated environment and returns a structured ExecutionResult.
"""

from __future__ import annotations

from engine.models import ExecutionResult, ResponseAction

from .account_actions import ACTIONS as ACCOUNT_ACTIONS
from .data_policy_actions import ACTIONS as DATA_POLICY_ACTIONS
from .environment import (
    ENTITY_LABELS,
    ENTITY_TYPES,
    SimulatedEnvironment,
    apply_change,
)
from .network_actions import ACTIONS as NETWORK_ACTIONS
from .process_actions import ACTIONS as PROCESS_ACTIONS

ALL_ACTIONS = {
    **ACCOUNT_ACTIONS,
    **NETWORK_ACTIONS,
    **PROCESS_ACTIONS,
    **DATA_POLICY_ACTIONS,
}


def available_actions() -> dict[str, str]:
    """Human labels for every implemented simulated action."""
    return {
        "disable_account": "Disable affected account",
        "lock_account": "Lock affected account",
        "revoke_session": "Revoke suspicious session",
        "restore_account": "Restore approved account status",
        "restrict_connection": "Restrict suspicious connection",
        "block_destination": "Block unauthorized destination",
        "isolate_endpoint": "Isolate affected endpoint",
        "terminate_process": "Terminate suspicious process",
        "isolate_process": "Isolate suspicious process",
        "quarantine_file": "Quarantine suspicious file",
        "restrict_transfer": "Restrict suspicious data transfer",
        "revoke_permissions": "Revoke unauthorized permissions",
        "restore_permissions": "Restore approved permissions",
        "apply_data_access_restriction": "Apply data-access restriction",
        "escalate_to_analyst": "Escalate to security administrator",
    }


def execute(env: SimulatedEnvironment, action: ResponseAction) -> ExecutionResult:
    """
    Execute one approved action against the simulated environment.

    Rejected actions never change state; the reason is captured in the result so
    the Explanation Facility can report *why* nothing happened.
    """
    handler = ALL_ACTIONS.get(action.action)
    if handler is None:
        result = ExecutionResult(
            action=action.action,
            label=action.label,
            target_type=action.target_type,
            target_id=action.target_id,
            success=False,
            message=f"No simulator is implemented for action {action.action!r}",
        )
    elif not action.executable:
        result = ExecutionResult(
            action=action.action,
            label=action.label,
            target_type=action.target_type,
            target_id=action.target_id,
            success=False,
            message=action.blocked_reason or "Action was not executable",
        )
    else:
        result = handler(env, action.target_id)

    action.execution = result
    action.status = "Executed" if result.success else "Rejected"
    return result


__all__ = [
    "ALL_ACTIONS",
    "ENTITY_LABELS",
    "ENTITY_TYPES",
    "SimulatedEnvironment",
    "apply_change",
    "available_actions",
    "execute",
]
