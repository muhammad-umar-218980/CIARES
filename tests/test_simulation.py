"""
Simulated execution tests: valid transitions, rejected transitions, missing
targets and actions that were blocked before execution.
"""

from __future__ import annotations

from engine.models import Phase, ResponseAction, Severity
from simulation import SimulatedEnvironment, execute


def make_action(
    action: str,
    target_type: str,
    target_id: str | None,
    executable: bool = True,
    phase: Phase = Phase.CONTAINMENT,
) -> ResponseAction:
    return ResponseAction(
        action=action,
        label=action.replace("_", " ").capitalize(),
        phase=phase,
        priority=1,
        target_type=target_type,
        target_id=target_id,
        finding_key="test_finding",
        finding_label="Test finding",
        finding_severity=Severity.HIGH,
        reason="Test action",
        executable=executable,
    )


# ---------------------------------------------------------------------------
# Successful transitions
# ---------------------------------------------------------------------------
def test_disable_account_changes_simulated_state():
    environment = SimulatedEnvironment()
    action = make_action("disable_account", "account", "USER-101")

    result = execute(environment, action)

    assert result.success is True
    assert environment.status_of("account", "USER-101") == "Disabled"
    assert action.status == "Executed"
    assert "Active" in result.before and "Disabled" in result.after


def test_revoke_session_changes_simulated_state():
    environment = SimulatedEnvironment()
    result = execute(environment, make_action("revoke_session", "session", "SESSION-204"))
    assert result.success is True
    assert environment.status_of("session", "SESSION-204") == "Revoked"


def test_restrict_transfer_changes_simulated_state():
    environment = SimulatedEnvironment()
    result = execute(environment, make_action("restrict_transfer", "transfer", "TRANSFER-301"))
    assert result.success is True
    assert environment.status_of("transfer", "TRANSFER-301") == "Restricted"


def test_permission_recovery_restores_the_baseline():
    environment = SimulatedEnvironment()
    environment.transition("account", "USER-101", "Revoked", {"Approved"}, field="permissions")

    result = execute(
        environment,
        make_action("restore_permissions", "account", "USER-101", phase=Phase.RECOVERY),
    )

    assert result.success is True
    assert environment.field_of("account", "USER-101", "permissions") == "Approved"


def test_escalation_does_not_need_a_simulated_entity():
    environment = SimulatedEnvironment()
    result = execute(
        environment,
        make_action("escalate_to_analyst", "incident", "INV-001", phase=Phase.ESCALATION),
    )
    assert result.success is True
    assert "INV-001" in result.message


# ---------------------------------------------------------------------------
# Rejections
# ---------------------------------------------------------------------------
def test_action_on_missing_entity_is_rejected():
    environment = SimulatedEnvironment()
    action = make_action("disable_account", "account", "USER-999")

    result = execute(environment, action)

    assert result.success is False
    assert "does not exist" in result.message
    assert action.status == "Rejected"


def test_action_without_a_target_is_rejected():
    environment = SimulatedEnvironment()
    result = execute(environment, make_action("disable_account", "account", None))
    assert result.success is False
    assert "no target identifier" in result.message


def test_second_disable_is_rejected_as_invalid_state():
    environment = SimulatedEnvironment()
    execute(environment, make_action("disable_account", "account", "USER-101"))
    result = execute(environment, make_action("disable_account", "account", "USER-101"))
    assert result.success is False
    assert "Disabled" in result.message


def test_blocked_action_is_not_executed():
    environment = SimulatedEnvironment()
    action = make_action("disable_account", "account", "USER-101", executable=False)
    action.blocked_reason = "Target check failed"

    result = execute(environment, action)

    assert result.success is False
    assert result.message == "Target check failed"
    assert environment.status_of("account", "USER-101") == "Active"


def test_unknown_action_is_rejected():
    environment = SimulatedEnvironment()
    result = execute(environment, make_action("launch_missiles", "account", "USER-101"))
    assert result.success is False
    assert "No simulator" in result.message


def test_snapshot_reflects_changes():
    environment = SimulatedEnvironment()
    execute(environment, make_action("disable_account", "account", "USER-101"))
    rows = environment.snapshot()
    account = next(row for row in rows if row["entity_id"] == "USER-101")
    assert account["status"] == "Disabled"
