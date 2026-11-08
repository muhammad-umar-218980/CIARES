"""
Forward-chaining tests: ordering, activation tracking, termination, provenance
and the prohibition on rewriting established facts.
"""

from __future__ import annotations

import pytest

from engine.inference_engine import InferenceEngine
from engine.working_memory import ContradictionError, WorkingMemory
from knowledge_base.authentication import AUTH_RULES


def run(observations=None, entities=None):
    memory = WorkingMemory(entities)
    memory.add_observations(observations or {})
    result = InferenceEngine(AUTH_RULES).run(memory)
    return memory, result


def full_compromise_observations() -> dict:
    return {
        "failed_login_attempts": 25,
        "successful_login_after_failures": True,
        "unusual_login_location": True,
    }


# ---------------------------------------------------------------------------
# Chaining
# ---------------------------------------------------------------------------
def test_forward_chaining_derives_conclusions_from_conclusions():
    memory, result = run(full_compromise_observations())
    order = [activation.rule.id for activation in result.activations]

    # AUTH-04 can only fire after AUTH-01..03 have inserted their conclusions.
    assert order.index("AUTH-01") < order.index("AUTH-04")
    assert order.index("AUTH-02") < order.index("AUTH-04")
    assert order.index("AUTH-03") < order.index("AUTH-04")
    assert memory.get("possible_account_compromise") is True


def test_inference_stops_at_the_fixed_point():
    _, result = run(full_compromise_observations())
    assert result.terminated_reason.startswith("fixed point")
    assert result.cycles == result.activation_count


def test_no_rule_fires_twice_for_the_same_supporting_facts():
    _, result = run(full_compromise_observations())
    rule_ids = [activation.rule.id for activation in result.activations]
    assert len(rule_ids) == len(set(rule_ids))


def test_empty_working_memory_activates_nothing():
    _, result = run({})
    assert result.activations == []
    assert result.terminated_reason.startswith("fixed point")


# ---------------------------------------------------------------------------
# Activation key
# ---------------------------------------------------------------------------
def test_activation_key_includes_entities_and_supporting_facts():
    rule = AUTH_RULES[0]
    memory = WorkingMemory({"account_id": "USER-101"})
    memory.add_observation("failed_login_attempts", 25)
    engine = InferenceEngine([rule])
    _, evaluations = engine.evaluate_rule(rule, memory)

    key_one = engine.activation_key(rule, memory.entities, evaluations)
    key_one_again = engine.activation_key(rule, {"account_id": "USER-101"}, evaluations)
    key_other_account = engine.activation_key(rule, {"account_id": "USER-202"}, evaluations)

    assert key_one == key_one_again
    assert key_one != key_other_account


# ---------------------------------------------------------------------------
# Working memory behaviour
# ---------------------------------------------------------------------------
def test_derived_fact_records_provenance():
    memory, _ = run(full_compromise_observations())
    fact = memory.get_fact("possible_account_compromise")

    assert fact is not None and fact.derived
    assert fact.rule_id == "AUTH-04"
    supporting = dict(fact.supporting)
    assert supporting["repeated_authentication_failures"] is True
    assert supporting["unusual_location_login"] is True

    # The provenance chain continues one hop back to the raw observation.
    origin = memory.provenance("unusual_location_login")
    assert origin["rule_id"] == "AUTH-03"
    assert origin["supporting"] == {"unusual_login_location": True}


def test_observations_cannot_overwrite_derived_facts():
    memory, _ = run(full_compromise_observations())
    with pytest.raises(ContradictionError):
        memory.add_observation("possible_account_compromise", False)


def test_contradictory_observations_are_rejected():
    memory = WorkingMemory()
    memory.add_observation("unusual_login_location", True)
    with pytest.raises(ContradictionError):
        memory.add_observation("unusual_login_location", False)


def test_unknown_facts_are_kept_out_of_the_known_fact_dict():
    memory = WorkingMemory()
    memory.add_observation("unusual_login_location", None)
    assert memory.is_known("unusual_login_location") is False
    assert memory.state("unusual_login_location") == "Unknown"
    assert "unusual_login_location" not in memory.as_dict()


def test_trace_records_start_and_finish():
    memory, _ = run(full_compromise_observations())
    kinds = [step["kind"] for step in memory.trace]
    assert kinds[0] == "observation"
    assert "start" in kinds
    assert "finish" in kinds
