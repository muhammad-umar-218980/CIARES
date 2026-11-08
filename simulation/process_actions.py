"""
Process and file response actions (Containment / Eradication).
"""

from __future__ import annotations

from engine.models import ExecutionResult

from .environment import apply_change


def terminate_process(env, target_id: str | None) -> ExecutionResult:
    return apply_change(
        env,
        action="terminate_process",
        label="Terminate suspicious process",
        entity_type="process",
        target_id=target_id,
        allowed_from=frozenset({"Running", "Isolated"}),
        new_value="Terminated",
    )


def isolate_process(env, target_id: str | None) -> ExecutionResult:
    return apply_change(
        env,
        action="isolate_process",
        label="Isolate suspicious process",
        entity_type="process",
        target_id=target_id,
        allowed_from=frozenset({"Running"}),
        new_value="Isolated",
    )


def quarantine_file(env, target_id: str | None) -> ExecutionResult:
    return apply_change(
        env,
        action="quarantine_file",
        label="Quarantine suspicious file",
        entity_type="file",
        target_id=target_id,
        allowed_from=frozenset({"Present"}),
        new_value="Quarantined",
    )


ACTIONS = {
    "terminate_process": terminate_process,
    "isolate_process": isolate_process,
    "quarantine_file": quarantine_file,
}
