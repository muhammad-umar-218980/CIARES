"""Default entity assignment for manual investigations."""

from __future__ import annotations

from engine.entities import default_entities, entity_key
from simulation.environment import ENTITY_TYPES, SimulatedEnvironment


def test_every_entity_type_receives_a_target():
    entities = default_entities()
    assert len(entities) == len(ENTITY_TYPES)
    for entity_type in ENTITY_TYPES:
        assert entity_key(entity_type) in entities


def test_assigned_targets_exist_in_the_inventory():
    environment = SimulatedEnvironment()
    entities = default_entities(environment)
    for key, identifier in entities.items():
        entity_type = key[: -len("_id")]
        assert environment.exists(entity_type, identifier)


def test_assignment_is_deterministic():
    assert default_entities() == default_entities()


def test_account_target_is_the_first_seeded_account():
    assert default_entities()["account_id"] == "USER-101"
