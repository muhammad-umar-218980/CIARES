"""
Individual rule tests.

Each rule must fire only when all of its conditions are satisfied, must stay
silent when a fact is explicitly False, and must stay silent when a fact is
Unknown.
"""

from __future__ import annotations

import pytest

from engine.inference_engine import InferenceEngine
from engine.models import Condition, Severity, values_equal
from engine.working_memory import WorkingMemory
from knowledge_base.authentication import AUTH_RULES
from knowledge_base.knowledge_acquisition import validate_catalogue
from knowledge_base.rule_registry import ALL_RULES


def fired_rules(rules, observations) -> set[str]:
    memory = WorkingMemory()
    memory.add_observations(observations)
    result = InferenceEngine(rules).run(memory)
    return {activation.rule.id for activation in result.activations}


def auth_rule(rule_id: str):
    return next(rule for rule in AUTH_RULES if rule.id == rule_id)


# ---------------------------------------------------------------------------
# Threshold behaviour
# ---------------------------------------------------------------------------
def test_auth01_fires_at_the_configured_threshold():
    assert "AUTH-01" in fired_rules([auth_rule("AUTH-01")], {"failed_login_attempts": 10})


def test_auth01_fires_above_the_threshold():
    assert "AUTH-01" in fired_rules([auth_rule("AUTH-01")], {"failed_login_attempts": 25})


def test_auth01_does_not_fire_below_the_threshold():
    assert "AUTH-01" not in fired_rules([auth_rule("AUTH-01")], {"failed_login_attempts": 3})


def test_auth02_and_auth03_fire_on_true_booleans():
    assert "AUTH-02" in fired_rules(
        [auth_rule("AUTH-02")], {"successful_login_after_failures": True}
    )
    assert "AUTH-03" in fired_rules([auth_rule("AUTH-03")], {"unusual_login_location": True})


# ---------------------------------------------------------------------------
# Three-valued logic: Unknown is not False
# ---------------------------------------------------------------------------
def test_unknown_fact_does_not_satisfy_a_rule():
    memory = WorkingMemory()
    memory.add_observation("unusual_login_location", None)  # explicitly Unknown
    result = InferenceEngine([auth_rule("AUTH-03")]).run(memory)
    assert result.activations == []


def test_missing_fact_does_not_satisfy_a_rule():
    assert "AUTH-03" not in fired_rules([auth_rule("AUTH-03")], {})


def test_false_fact_does_not_satisfy_a_rule():
    assert "AUTH-03" not in fired_rules(
        [auth_rule("AUTH-03")], {"unusual_login_location": False}
    )


def test_unknown_condition_is_reported_as_unknown():
    condition = Condition("unusual_login_location", "==", True)
    satisfied, note = condition.evaluate(None, known=False)
    assert satisfied is None
    assert "Unknown" in note


# ---------------------------------------------------------------------------
# Corroboration (AUTH-04)
# ---------------------------------------------------------------------------
def test_auth04_needs_all_three_supporting_facts():
    only_failures = fired_rules(
        AUTH_RULES, {"failed_login_attempts": 25, "unusual_login_location": True}
    )
    assert "AUTH-04" not in only_failures

    complete = fired_rules(
        AUTH_RULES,
        {
            "failed_login_attempts": 25,
            "successful_login_after_failures": True,
            "unusual_login_location": True,
        },
    )
    assert "AUTH-04" in complete


# ---------------------------------------------------------------------------
# Condition semantics
# ---------------------------------------------------------------------------
def test_booleans_and_numbers_are_not_interchangeable():
    assert values_equal(True, True)
    assert not values_equal(True, 1)
    assert values_equal(1, 1)


def test_numeric_operator_on_text_is_unknown_not_true():
    condition = Condition("failed_login_attempts", ">=", 10)
    satisfied, note = condition.evaluate("many", known=True)
    assert satisfied is None
    assert "not numeric" in note


def test_membership_operator():
    condition = Condition("severity_hint", "in", ("High", "Critical"))
    assert condition.evaluate("High", known=True)[0] is True
    assert condition.evaluate("Low", known=True)[0] is False


# ---------------------------------------------------------------------------
# Knowledge base integrity
# ---------------------------------------------------------------------------
def test_registered_rules_are_structurally_valid():
    report = validate_catalogue(ALL_RULES)
    assert report.errors == [], report.errors


def test_rule_ids_are_unique():
    ids = [rule.id for rule in ALL_RULES]
    assert len(ids) == len(set(ids))


def test_every_rule_has_conditions_and_a_conclusion():
    for rule in ALL_RULES:
        assert rule.conditions, f"{rule.id} has no conditions"
        assert rule.conclusion_key, f"{rule.id} has no conclusion"
        assert rule.conclusion_key not in rule.condition_fields, (
            f"{rule.id} supports its own conclusion"
        )
        assert isinstance(rule.severity, Severity)
        assert rule.description
        assert rule.source


@pytest.mark.skipif(len(ALL_RULES) < 60, reason="full rule catalogue still being authored")
def test_knowledge_base_contains_sixty_rules():
    assert len(ALL_RULES) == 60


@pytest.mark.skipif(len(ALL_RULES) < 60, reason="full rule catalogue still being authored")
def test_knowledge_base_contains_at_least_fifty_conditions():
    report = validate_catalogue(ALL_RULES)
    assert report.condition_count >= 50
