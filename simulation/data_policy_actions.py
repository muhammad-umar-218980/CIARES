"""
Data and permission response actions (Containment / Recovery).
"""

from __future__ import annotations

from engine.models import ExecutionResult

from .environment import apply_change


def restrict_transfer(env, target_id: str | None) -> ExecutionResult:
    return apply_change(
        env,
        action="restrict_transfer",
        label="Restrict suspicious data transfer",
        entity_type="transfer",
        target_id=target_id,
        allowed_from=frozenset({"Active"}),
        new_value="Restricted",
    )


def revoke_permissions(env, target_id: str | None) -> ExecutionResult:
    return apply_change(
        env,
        action="revoke_permissions",
        label="Revoke unauthorized permissions",
        entity_type="account",
        target_id=target_id,
        allowed_from=frozenset({"Approved", "Elevated"}),
        new_value="Revoked",
        field="permissions",
    )


def restore_permissions(env, target_id: str | None) -> ExecutionResult:
    return apply_change(
        env,
        action="restore_permissions",
        label="Restore approved permissions",
        entity_type="account",
        target_id=target_id,
        allowed_from=frozenset({"Revoked", "Elevated"}),
        new_value="Approved",
        field="permissions",
    )


def apply_data_access_restriction(env, target_id: str | None) -> ExecutionResult:
    return apply_change(
        env,
        action="apply_data_access_restriction",
        label="Apply data-access restriction",
        entity_type="account",
        target_id=target_id,
        allowed_from=frozenset({"Unrestricted"}),
        new_value="Restricted",
        field="data_access",
    )


ACTIONS = {
    "restrict_transfer": restrict_transfer,
    "revoke_permissions": revoke_permissions,
    "restore_permissions": restore_permissions,
    "apply_data_access_restriction": apply_data_access_restriction,
}
