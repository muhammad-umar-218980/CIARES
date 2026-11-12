"""
Complete-investigation tests: a scenario must run end to end through the same
pipeline the Streamlit portal uses, from observations to a written response plan.
"""

from __future__ import annotations

import json
import re

import pytest

from engine.pipeline import run_investigation
from engine.report import (
    approve,
    evidence_rows,
    plan_steps,
    plan_text,
    reasoning_paragraphs,
    threat_score,
    threat_sentence,
)
from knowledge_base.rule_registry import ALL_RULES
from scenarios.sample_scenarios import SCENARIOS, get_scenario

SCENARIO_IDS = [scenario.id for scenario in SCENARIOS]
RULE_ID = re.compile(r"\b(AUTH|MAL|NET|DATA|POL)-\d{2}\b")


def run(scenario_id: str):
    scenario = get_scenario(scenario_id)
    return run_investigation(
        scenario.observations,
        name=scenario.name,
        scenario_id=scenario.id,
    )


@pytest.mark.parametrize("scenario_id", SCENARIO_IDS)
def test_every_scenario_runs_without_error(scenario_id):
    investigation = run(scenario_id)
    assert investigation.id.startswith("INV-")
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
    assert action.phase.value == "Containment"
    assert action.deferred is False


def test_missing_evidence_prevents_the_compromise_finding():
    scenario = get_scenario("SCN-001")
    observations = dict(scenario.observations)
    observations.pop("unusual_login_location", None)

    investigation = run_investigation(observations, name="Incomplete evidence")

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
# The public narrative: prose, not rule identifiers
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("scenario_id", SCENARIO_IDS)
def test_public_narrative_hides_rule_identifiers(scenario_id):
    investigation = run(scenario_id)
    narrative = " ".join(reasoning_paragraphs(investigation))
    assert narrative
    assert RULE_ID.search(narrative) is None

    sentence = threat_sentence(investigation)
    assert RULE_ID.search(sentence) is None
    assert "Threat level" in sentence

    score = threat_score(investigation)
    assert 0 <= score <= 100


@pytest.mark.parametrize("scenario_id", SCENARIO_IDS)
def test_evidence_table_keeps_the_rule_identifiers_for_administration(scenario_id):
    investigation = run(scenario_id)
    rows = evidence_rows(investigation)
    assert rows
    assert all(RULE_ID.match(str(row["Rule"])) for row in rows)


# ---------------------------------------------------------------------------
# Approval and the written response plan
# ---------------------------------------------------------------------------
def test_approval_only_covers_the_selected_recommendations():
    investigation = run("SCN-005")
    ready = [action for action in investigation.actions if not action.deferred]
    assert len(ready) >= 2

    approved = approve(investigation, [ready[0].action_id])

    assert [action.action_id for action in approved] == [ready[0].action_id]
    assert investigation.approved_at
    assert len(investigation.approved_actions) == 1


def test_deferred_recovery_cannot_be_approved():
    investigation = run("SCN-005")
    deferred = [action for action in investigation.actions if action.deferred]
    assert deferred, "SCN-005 should defer a recovery action"

    approve(investigation, [action.action_id for action in deferred])
    assert investigation.approved_actions == []


def test_response_plan_is_written_after_approval():
    investigation = run("SCN-001")
    approve(investigation, [action.action_id for action in investigation.actions])

    steps = plan_steps(investigation)
    assert steps
    assert all(step.endswith(".") for step in steps)

    text = plan_text(investigation)
    assert "CIARES RESPONSE PLAN" in text
    assert investigation.id in text
    assert "APPROVED RESPONSE" in text
