"""
Default entity assignment for manual investigations.

An analyst should not have to type database identifiers to describe an
incident. Every manual investigation is therefore attached to the first entity
of each type in the simulated inventory, which keeps every response target
valid by construction.

This is deliberately *not* random ID generation: the Decision Engine validates
targets against the simulated world, so an invented identifier would make every
action non-executable. Scenarios keep their own entity maps.
"""

from __future__ import annotations

from simulation.environment import ENTITY_TYPES, SimulatedEnvironment


def entity_key(entity_type: str) -> str:
    """Map an entity type to the key used in an investigation's entity map."""
    return f"{entity_type}_id"


def default_entities(environment: SimulatedEnvironment | None = None) -> dict[str, str]:
    """Return one valid target per entity type, taken from the inventory."""
    environment = environment or SimulatedEnvironment()
    entities: dict[str, str] = {}
    for entity_type in ENTITY_TYPES:
        identifiers = sorted(environment.entities.get(entity_type, {}))
        if identifiers:
            entities[entity_key(entity_type)] = identifiers[0]
    return entities
