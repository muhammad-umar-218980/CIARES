"""
Account and session response actions (Containment / Recovery).
"""

from __future__ import annotations

from engine.models import ExecutionResult

from .environment import apply_change

DISABLE_FROM = frozenset({"Active", "Locked"})
LOCK_FROM = frozenset({"Active"})
REVOKE_FROM = frozenset({"Active"})
RESTORE_FROM = frozenset({"Disabled", "Locked"})


def disable_account(env, target_id: str | None) -> ExecutionResult:
    return apply_change(
        env,
        action="disable_account",
        label="Disable affected account",
        entity_type="account",
        target_id=target_id,
        allowed_from=DISABLE_FROM,
        new_value="Disabled",
    )


def lock_account(env, target_id: str | None) -> ExecutionResult:
    return apply_change(
        env,
        action="lock_account",
        label="Lock affected account",
        entity_type="account",
        target_id=target_id,
        allowed_from=LOCK_FROM,
        new_value="Locked",
    )


def revoke_session(env, target_id: str | None) -> ExecutionResult:
    return apply_change(
        env,
        action="revoke_session",
        label="Revoke suspicious session",
        entity_type="session",
        target_id=target_id,
        allowed_from=REVOKE_FROM,
        new_value="Revoked",
    )


def restore_account(env, target_id: str | None) -> ExecutionResult:
    return apply_change(
        env,
        action="restore_account",
        label="Restore approved account status",
        entity_type="account",
        target_id=target_id,
        allowed_from=RESTORE_FROM,
        new_value="Active",
    )


def escalate_to_analyst(env, target_id: str | None) -> ExecutionResult:
    """Escalation does not change simulated state; it records the referral."""
    return ExecutionResult(
        action="escalate_to_analyst",
        label="Escalate to security administrator",
        target_type="incident",
        target_id=target_id,
        success=True,
        message=f"Investigation {target_id or '(unnamed)'} referred to a security administrator",
    )


ACTIONS = {
    "disable_account": disable_account,
    "lock_account": lock_account,
    "revoke_session": revoke_session,
    "restore_account": restore_account,
    "escalate_to_analyst": escalate_to_analyst,
}
