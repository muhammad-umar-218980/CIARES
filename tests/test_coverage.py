"""
Catalogue-completeness tests.

These are the guards that stop the knowledge base from degrading into padding:
every registered rule must be structurally valid *and* must actually fire in at
least one shipped scenario, so a rule that can never activate fails the suite.
"""

from __future__ import annotations

from collections import Counter

import pytest

from engine.pipeline import run_investigation
from knowledge_base.knowledge_acquisition import validate_catalogue
from knowledge_base.rule_registry import ALL_RULES, MODULES, RULES_BY_MODULE
from scenarios.sample_scenarios import SCENARIOS
from simulation import execute

EXPECTED_RULES = 60
EXPECTED_PER_MODULE = 12
MINIMUM_CONDITIONS = 50


@pytest.fixture(scope="module")
def investigations():
    return {
        scenario.id: run_investigation(
            scenario.observations,
            scenario.entities,
            scenario.name,
            scenario_id=scenario.id,
        )
        for scenario in SCENARIOS
    }


@pytest.fixture(scope="module")
def fired_rule_ids(investigations):
    fired: set[str] = set()
    for investigation in investigations.values():
        fired.update(activation.rule.id for activation in investigation.activations)
    return fired


# ---------------------------------------------------------------------------
# Catalogue size
# ---------------------------------------------------------------------------
def test_exactly_sixty_rules_are_registered():
    assert len(ALL_RULES) == EXPECTED_RULES


def test_each_of_the_five_modules_has_twelve_rules():
    counts = Counter(rule.module for rule in ALL_RULES)
    assert len(MODULES) == 5
    for module in MODULES:
        assert counts[module] == EXPECTED_PER_MODULE, (module, counts[module])


def test_at_least_fifty_logical_conditions_are_registered():
    report = validate_catalogue(ALL_RULES)
    assert report.condition_count >= MINIMUM_CONDITIONS
    assert report.distinct_condition_fields >= MINIMUM_CONDITIONS


def test_the_catalogue_has_no_validation_errors_or_warnings():
    report = validate_catalogue(ALL_RULES)
    assert report.errors == [], report.errors
    assert report.warnings == [], report.warnings


def test_rule_ids_are_unique_and_follow_the_module_pattern():
    ids = [rule.id for rule in ALL_RULES]
    assert len(ids) == len(set(ids))
    for rule in ALL_RULES:
        prefix = rule.id.split("-")[0]
        assert prefix in {"AUTH", "MAL", "NET", "DATA", "POL"}
        assert rule.conditions, rule.id
        assert rule.conclusion_key not in rule.condition_fields, rule.id


# ---------------------------------------------------------------------------
# Reachability: no cosmetic rules
# ---------------------------------------------------------------------------
def test_every_rule_fires_in_at_least_one_shipped_scenario(fired_rule_ids):
    never_fired = sorted(rule.id for rule in ALL_RULES if rule.id not in fired_rule_ids)
    assert never_fired == [], (
        "these rules can never activate in any shipped scenario: " + ", ".join(never_fired)
    )


def test_every_module_has_at_least_one_critical_finding(investigations):
    for module in MODULES:
        critical = {
            finding.key
            for investigation in investigations.values()
            for finding in investigation.findings
            if finding.module == module and finding.severity.value == "Critical"
        }
        assert critical, f"{module} never produces a critical finding"


def test_every_scenario_derives_its_expected_findings(investigations):
    for scenario in SCENARIOS:
        derived = {finding.key for finding in investigations[scenario.id].findings}
        missing = set(scenario.expected_findings) - derived
        assert missing == set(), f"{scenario.id} missing {sorted(missing)}"


# ---------------------------------------------------------------------------
# Findings -> responses
# ---------------------------------------------------------------------------
def test_every_actionable_rule_produces_a_matching_response(investigations):
    actionable = {rule.recommended_action for rule in ALL_RULES if rule.recommended_action}
    proposed = {
        action.action
        for investigation in investigations.values()
        for action in investigation.actions
    }
    assert actionable == proposed


def test_every_executable_action_succeeds_in_the_simulation(investigations):
    executed = 0
    for investigation in investigations.values():
        for action in investigation.actions:
            if not action.executable:
                continue
            result = execute(investigation.environment, action)
            assert result.success is True, (investigation.id, action.action, result.message)
            executed += 1
    assert executed > 0


def test_containment_precedes_recovery_and_escalation(investigations):
    order = {"Containment": 1, "Eradication": 2, "Recovery": 3, "Escalation": 4}
    for investigation in investigations.values():
        phases = [order[action.phase.value] for action in investigation.actions]
        assert phases == sorted(phases), investigation.id


# ---------------------------------------------------------------------------
# Explanation completeness
# ---------------------------------------------------------------------------
def test_every_activation_records_all_conditions_as_satisfied(investigations):
    for investigation in investigations.values():
        for activation in investigation.activations:
            assert activation.evaluations, (investigation.id, activation.rule.id)
            for evaluation in activation.evaluations:
                assert evaluation.satisfied is True, (
                    investigation.id,
                    activation.rule.id,
                    evaluation.condition.field,
                )
                assert evaluation.note


def test_every_derived_fact_records_its_rule_and_support(investigations):
    for investigation in investigations.values():
        memory = investigation.memory
        for fact in memory.derived_facts():
            assert fact.rule_id, fact.key
            assert fact.supporting, fact.key
            assert all(key != fact.key for key, _ in fact.supporting)
