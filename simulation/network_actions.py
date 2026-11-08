"""
Network response actions (Containment).

Each function performs one state transition in the simulated environment and
returns a structured ExecutionResult.
"""

from __future__ import annotations

from engine.models import ExecutionResult

from .environment import apply_change


def restrict_connection(env, target_id: str | None) -> ExecutionResult:
    return apply_change(
        env,
        action="restrict_connection",
        label="Restrict suspicious connection",
        entity_type="connection",
        target_id=target_id,
        allowed_from=frozenset({"Open"}),
        new_value="Restricted",
    )


def block_destination(env, target_id: str | None) -> ExecutionResult:
    return apply_change(
        env,
        action="block_destination",
        label="Block unauthorized destination",
        entity_type="destination",
        target_id=target_id,
        allowed_from=frozenset({"Reachable"}),
        new_value="Blocked",
    )


def isolate_endpoint(env, target_id: str | None) -> ExecutionResult:
    return apply_change(
        env,
        action="isolate_endpoint",
        label="Isolate affected endpoint",
        entity_type="endpoint",
        target_id=target_id,
        allowed_from=frozenset({"Online"}),
        new_value="Isolated",
    )


ACTIONS = {
    "restrict_connection": restrict_connection,
    "block_destination": block_destination,
    "isolate_endpoint": isolate_endpoint,
}
