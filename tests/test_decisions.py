"""
Decision Engine tests: recommendation selection, duplicate collapsing,
containment/recovery deferral and phase ordering.

The Decision Engine is pure policy. It never validates a target or executes
anything, because CIARES advises a human and does not act on a real network.
"""

from __future__ import annotations

from engine.decision_engine import ACTION_LIBRARY, DecisionEngine
from engine.models import Finding, Phase, Severity
from knowledge_base.rule_registry import ALL_RULES


def finding(
    key: str,
    *,
    action: str | None = "disable_account",
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
    )


def test_actionable_finding_produces_a_recommendation():
    actions = DecisionEngine().decide([finding("possible_account_compromise")])

    assert len(actions) == 1
    action = actions[0]
    assert action.action == "disable_account"
    assert action.phase is Phase.CONTAINMENT
    assert action.action_id == "ACT-001"
    assert action.approved is False
    assert action.deferred is False
    assert "possible account compromise" in action.reason.lower()


def test_diagnostic_only_finding_produces_nothing():
    actions = DecisionEngine().decide([finding("repeated_authentication_failures", action=None)])
    assert actions == []


def test_duplicate_actions_are_collapsed_and_keep_the_strongest_severity():
    actions = DecisionEngine().decide(
        [
            finding("first_reason", severity=Severity.MEDIUM, sequence=1),
            finding("second_reason", severity=Severity.CRITICAL, sequence=2),
        ]
    )

    assert len(actions) == 1
    action = actions[0]
    assert action.finding_severity is Severity.CRITICAL
    assert "first reason" in action.reason.lower()
    assert "second reason" in action.reason.lower()


def test_recovery_is_deferred_while_containment_is_open():
    actions = DecisionEngine().decide(
        [
            finding("contained", action="disable_account", phase=Phase.CONTAINMENT),
            finding("recover", action="restore_account", phase=Phase.RECOVERY, sequence=2),
        ]
    )

    recovery = next(action for action in actions if action.action == "restore_account")
    assert recovery.deferred is True
    assert recovery.is_applicable is False
    assert "containment" in recovery.defer_reason.lower()


def test_recovery_is_not_deferred_when_there_is_no_containment():
    actions = DecisionEngine().decide(
        [finding("recover", action="restore_account", phase=Phase.RECOVERY)]
    )
    assert actions[0].deferred is False


def test_actions_are_ordered_by_phase_then_priority():
    actions = DecisionEngine().decide(
        [
            finding("escalate", action="escalate_to_analyst", phase=Phase.ESCALATION),
            finding("quarantine", action="quarantine_file", phase=Phase.ERADICATION, sequence=2),
            finding("disable", action="disable_account", phase=Phase.CONTAINMENT, sequence=3),
            finding("revoke", action="revoke_session", phase=Phase.CONTAINMENT, sequence=4),
        ]
    )

    assert [action.action for action in actions] == [
        "disable_account",
        "revoke_session",
        "quarantine_file",
        "escalate_to_analyst",
    ]
    assert [action.action_id for action in actions] == [
        "ACT-001",
        "ACT-002",
        "ACT-003",
        "ACT-004",
    ]


def test_every_actionable_rule_names_a_known_action():
    unknown = sorted(
        {
            rule.recommended_action
            for rule in ALL_RULES
            if rule.recommended_action and rule.recommended_action not in ACTION_LIBRARY
        }
    )
    assert unknown == [], f"actions missing from the catalogue: {unknown}"


def test_every_catalogue_action_has_a_phase_and_a_description():
    for key, spec in ACTION_LIBRARY.items():
        assert spec.key == key
        assert spec.label
        assert isinstance(spec.phase, Phase)
        assert spec.priority >= 1
        assert spec.description.endswith("."), key
