"""
Complete-investigation tests: a scenario must run end to end through the same
pipeline the Streamlit UI uses, from observations to simulated execution.
"""

from __future__ import annotations

import json

import pytest

from engine.pipeline import run_investigation
from knowledge_base.rule_registry import ALL_RULES
from scenarios.sample_scenarios import SCENARIOS, get_scenario
from simulation import execute

SCENARIO_IDS = [scenario.id for scenario in SCENARIOS]


def run(scenario_id: str):
    scenario = get_scenario(scenario_id)
    return run_investigation(
        scenario.observations,
        scenario.entities,
        scenario.name,
        scenario_id=scenario.id,
    )


@pytest.mark.parametrize("scenario_id", SCENARIO_IDS)
def test_every_scenario_runs_without_error(scenario_id):
    investigation = run(scenario_id)
    assert investigation.id.startswith("INV-")
    assert investigation.environment is not None
    if len(ALL_RULES) >= 60:
        assert investigation.activations


@pytest.mark.parametrize("scenario_id", SCENARIO_IDS)
def test_investigation_records_are_json_serialisable(scenario_id):
    investigation = run(scenario_id)
    payload = json.dumps(investigation.to_record())
    assert investigation.id in payload


@pytest.mark.parametrize("scenario_id", SCENARIO_IDS)
def test_scenarios_never_preload_a_diagnosis(scenario_id):
    scenario = get_scenario(scenario_id)
    conclusions = {rule.conclusion_key for rule in ALL_RULES}
    leaked = conclusions.intersection(scenario.observations)
    assert leaked == set(), f"{scenario_id} preloads derived facts: {leaked}"


# ---------------------------------------------------------------------------
# SCN-001: the reference account-compromise investigation
# ---------------------------------------------------------------------------
def test_account_compromise_scenario_derives_expected_findings():
    investigation = run("SCN-001")
    derived = {finding.key for finding in investigation.findings}
    expected = set(get_scenario("SCN-001").expected_findings)

    assert expected.issubset(derived), expected - derived
    assert "AUTH-04" in {activation.rule.id for activation in investigation.activations}


def test_account_compromise_scenario_recommends_disabling_the_account():
    investigation = run("SCN-001")
    action = next(
        action for action in investigation.actions if action.action == "disable_account"
    )
    assert action.target_id == "USER-101"
    assert action.executable is True


def test_account_compromise_response_executes_in_the_simulation():
    investigation = run("SCN-001")
    action = next(
        action for action in investigation.actions if action.action == "disable_account"
    )

    result = execute(investigation.environment, action)

    assert result.success is True
    assert investigation.environment.status_of("account", "USER-101") == "Disabled"
    assert action.status == "Executed"


def test_missing_evidence_prevents_the_compromise_finding():
    scenario = get_scenario("SCN-001")
    observations = dict(scenario.observations)
    observations.pop("unusual_login_location", None)

    investigation = run_investigation(
        observations, scenario.entities, "Incomplete evidence"
    )

    derived = {finding.key for finding in investigation.findings}
    assert "possible_account_compromise" not in derived
    assert "unusual_location_login" not in derived


@pytest.mark.parametrize("scenario_id", SCENARIO_IDS)
def test_expected_chains_are_met_once_the_modules_are_authored(scenario_id):
    if len(ALL_RULES) < 60:
        pytest.skip("knowledge base still being authored")

    investigation = run(scenario_id)
    derived = {finding.key for finding in investigation.findings}
    expected = set(get_scenario(scenario_id).expected_findings)
    assert expected.issubset(derived), expected - derived


# ---------------------------------------------------------------------------
# Target validation through the real pipeline
# ---------------------------------------------------------------------------
def test_pipeline_rejects_a_target_that_does_not_exist():
    investigation = run_investigation(
        {
            "failed_login_attempts": 25,
            "successful_login_after_failures": True,
            "unusual_login_location": True,
        },
        {"account_id": "USER-999"},
        "Invalid target investigation",
    )

    action = next(
        action for action in investigation.actions if action.action == "disable_account"
    )
    assert action.executable is False
    assert "does not exist" in action.blocked_reason

    result = execute(investigation.environment, action)
    assert result.success is False
    assert "does not exist" in result.message


def test_pipeline_keeps_the_seeded_target_executable():
    investigation = run_investigation(
        {
            "failed_login_attempts": 25,
            "successful_login_after_failures": True,
            "unusual_login_location": True,
        },
        {"account_id": "USER-101"},
        "Valid target investigation",
    )

    action = next(
        action for action in investigation.actions if action.action == "disable_account"
    )
    assert action.executable is True
    assert action.blocked_reason == ""
