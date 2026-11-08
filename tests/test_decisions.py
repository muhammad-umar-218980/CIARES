"""
Decision Engine tests: action selection, target validation, duplicate collapsing
and containment/recovery conflict resolution.
"""

from __future__ import annotations

from engine.decision_engine import ACTION_LIBRARY, DecisionEngine
from engine.models import Finding, Phase, Severity
from knowledge_base.rule_registry import ALL_RULES
from simulation import ALL_ACTIONS, SimulatedEnvironment


def finding(
    key: str,
    *,
    action: str | None = "disable_account",
    entity_type: str | None = "account",
    severity: Severity = Severity.CRITICAL,
    sequence: int = 1,
    phase: Phase = Phase.CONTAINMENT,
) -> Finding:
    return Finding(
        key=key,
        label=key.replace("_", " ").capitalize(),
        severity=severity,
        module="Test Module",
        rule_ids=["TST-01"],
        sequence=sequence,
        recommended_action=action,
        action_phase=phase,
        entity_type=entity_type,
    )


def test_finding_produces_a_targeted_containment_action():
    actions = DecisionEngine(SimulatedEnvironment()).decide(
        [finding("possible_account_compromise")], {"account_id": "USER-101"}
    )
    assert len(actions) == 1
    action = actions[0]
    assert action.action == "disable_account"
    assert action.target_id == "USER-101"
    assert action.phase is Phase.CONTAINMENT
    assert action.executable is True
    assert "possible account compromise" in action.reason.lower()


def test_findings_without_a_recommended_action_produce_no_response():
    actions = DecisionEngine(SimulatedEnvironment()).decide(
        [finding("repeated_authentication_failures", action=None, entity_type=None)],
        {"account_id": "USER-101"},
    )
    assert actions == []


def test_missing_target_identifier_blocks_the_action():
    actions = DecisionEngine(SimulatedEnvironment()).decide(
        [finding("possible_account_compromise")], {}
    )
    assert actions[0].executable is False
    assert "identifier" in actions[0].blocked_reason


def test_non_existent_target_blocks_the_action():
    actions = DecisionEngine(SimulatedEnvironment()).decide(
        [finding("possible_account_compromise")], {"account_id": "USER-999"}
    )
    assert actions[0].executable is False
    assert "does not exist" in actions[0].blocked_reason


def test_target_in_wrong_state_blocks_the_action():
    environment = SimulatedEnvironment()
    environment.transition("account", "USER-101", "Disabled", {"Active"})
    actions = DecisionEngine(environment).decide(
        [finding("possible_account_compromise")], {"account_id": "USER-101"}
    )
    assert actions[0].executable is False
    assert "Disabled" in actions[0].blocked_reason


def test_duplicate_actions_are_collapsed_into_one():
    duplicate = finding("account_compromise_indicator", sequence=2)
    actions = DecisionEngine(SimulatedEnvironment()).decide(
        [finding("possible_account_compromise", sequence=1), duplicate],
        {"account_id": "USER-101"},
    )
    assert len(actions) == 1
    assert "also recommended" in actions[0].reason


def test_recovery_is_suppressed_when_containment_targets_the_same_account():
    environment = SimulatedEnvironment()
    environment.transition("account", "USER-101", "Elevated", {"Approved"}, field="permissions")
    contain = finding("possible_account_compromise", sequence=1)
    recover = finding(
        "permission_violation",
        action="restore_permissions",
        sequence=2,
        phase=Phase.RECOVERY,
        severity=Severity.HIGH,
    )
    actions = DecisionEngine(environment).decide(
        [contain, recover], {"account_id": "USER-101"}
    )
    recovery = next(action for action in actions if action.action == "restore_permissions")
    assert recovery.executable is False
    assert recovery.status == "Skipped"
    assert "containment" in recovery.blocked_reason.lower()


def test_actions_are_ordered_by_phase_then_priority():
    actions = DecisionEngine(SimulatedEnvironment()).decide(
        [
            finding("a", action="restore_account", phase=Phase.RECOVERY, sequence=1),
            finding("b", action="revoke_session", entity_type="session", sequence=2),
            finding("c", action="disable_account", sequence=3),
        ],
        {"account_id": "USER-101", "session_id": "SESSION-204"},
    )
    phases = [action.phase.order for action in actions]
    assert phases == sorted(phases)
    assert [action.action for action in actions][0] == "disable_account"


# ---------------------------------------------------------------------------
# Catalogue consistency
# ---------------------------------------------------------------------------
def test_action_library_and_simulation_handlers_agree():
    assert set(ACTION_LIBRARY) == set(ALL_ACTIONS)


def test_every_recommended_action_in_the_knowledge_base_is_implemented():
    for rule in ALL_RULES:
        if rule.recommended_action:
            assert rule.recommended_action in ACTION_LIBRARY, rule.id
            assert rule.recommended_action in ALL_ACTIONS, rule.id


def test_action_identifiers_are_formatted():
    actions = DecisionEngine(SimulatedEnvironment()).decide(
        [finding("possible_account_compromise")], {"account_id": "USER-101"}
    )
    assert actions[0].action_id.startswith("ACT-")
