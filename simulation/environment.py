"""
The simulated environment that response actions act upon.

CIARES never touches a real account, session, process or network. It keeps a
small in-memory world of simulated entities (accounts, sessions, processes,
files, transfers, destinations, endpoints, connections) whose state can be
changed by the action modules. Every action validates the target first, so a
response aimed at a non-existent entity is rejected with a reason instead of
silently succeeding.
"""

from __future__ import annotations

from typing import Any

from engine.models import ExecutionResult

ENTITY_TYPES: tuple[str, ...] = (
    "account",
    "session",
    "process",
    "file",
    "transfer",
    "destination",
    "endpoint",
    "connection",
)

ENTITY_LABELS: dict[str, str] = {
    "account": "Account",
    "session": "Session",
    "process": "Process",
    "file": "File",
    "transfer": "Transfer",
    "destination": "Destination",
    "endpoint": "Endpoint",
    "connection": "Connection",
}

DEFAULT_STATUS: dict[str, str] = {
    "account": "Active",
    "session": "Active",
    "process": "Running",
    "file": "Present",
    "transfer": "Active",
    "destination": "Reachable",
    "endpoint": "Online",
    "connection": "Open",
}

SEED_ENTITIES: dict[str, dict[str, dict[str, Any]]] = {
    "account": {
        "USER-101": {"status": "Active", "permissions": "Approved", "data_access": "Unrestricted"},
        "USER-202": {"status": "Active", "permissions": "Approved", "data_access": "Unrestricted"},
    },
    "session": {"SESSION-204": {"status": "Active"}, "SESSION-311": {"status": "Active"}},
    "process": {"PROCESS-401": {"status": "Running"}},
    "file": {"FILE-501": {"status": "Present"}},
    "transfer": {"TRANSFER-301": {"status": "Active"}},
    "destination": {"DEST-901": {"status": "Reachable"}},
    "endpoint": {"ENDPOINT-701": {"status": "Online"}},
    "connection": {"CONN-801": {"status": "Open"}},
}


class SimulatedEnvironment:
    def __init__(self, seed: bool = True) -> None:
        self.entities: dict[str, dict[str, dict[str, Any]]] = {
            entity_type: {} for entity_type in ENTITY_TYPES
        }
        if seed:
            self.seed_defaults()

    # -- lifecycle ----------------------------------------------------------
    def seed_defaults(self) -> None:
        for entity_type, entities in SEED_ENTITIES.items():
            for entity_id, state in entities.items():
                self.entities[entity_type][entity_id] = dict(state)

    def provision(
        self, entity_type: str, entity_id: str | None, status: str | None = None
    ) -> dict[str, Any] | None:
        """Create (or return) a simulated entity, e.g. one named in a scenario."""
        if not entity_id:
            return None
        if entity_type not in self.entities:
            raise ValueError(f"Unknown entity type {entity_type!r}")
        if entity_id not in self.entities[entity_type]:
            self.entities[entity_type][entity_id] = {
                "status": status or DEFAULT_STATUS[entity_type]
            }
        return self.entities[entity_type][entity_id]

    def provision_from_entities(self, entities: dict[str, str]) -> None:
        """Provision every ``<type>_id`` entry in an investigation's entity map."""
        for key, value in entities.items():
            if not key.endswith("_id") or not value:
                continue
            entity_type = key[: -len("_id")]
            if entity_type in self.entities:
                self.provision(entity_type, value)

    # -- reading ------------------------------------------------------------
    def exists(self, entity_type: str, entity_id: str | None) -> bool:
        return bool(entity_id) and entity_id in self.entities.get(entity_type, {})

    def get(self, entity_type: str, entity_id: str) -> dict[str, Any] | None:
        return self.entities.get(entity_type, {}).get(entity_id)

    def status_of(self, entity_type: str, entity_id: str) -> str | None:
        entity = self.get(entity_type, entity_id)
        return None if entity is None else str(entity.get("status", ""))

    def field_of(self, entity_type: str, entity_id: str, field: str) -> Any:
        entity = self.get(entity_type, entity_id)
        return None if entity is None else entity.get(field)

    def snapshot(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for entity_type in ENTITY_TYPES:
            for entity_id, state in sorted(self.entities[entity_type].items()):
                rows.append(
                    {
                        "entity_type": entity_type,
                        "entity_id": entity_id,
                        "status": state.get("status", ""),
                        "permissions": state.get("permissions", ""),
                    }
                )
        return rows

    # -- mutation -----------------------------------------------------------
    def transition(
        self,
        entity_type: str,
        entity_id: str | None,
        new_value: str,
        allowed_from: set[str] | frozenset[str],
        field: str = "status",
    ) -> tuple[bool, str, str, str]:
        """
        Apply a validated state change.

        Returns (ok, before, after, reason). The reason explains a rejection in
        words the UI can show to the user.
        """
        label = ENTITY_LABELS.get(entity_type, entity_type.title())
        if not entity_id:
            return False, "", "", f"{label} action rejected: no target identifier was provided"
        if not self.exists(entity_type, entity_id):
            return (
                False,
                "",
                "",
                f"{label} {entity_id} does not exist in the simulated environment",
            )

        entity = self.entities[entity_type][entity_id]
        current = str(entity.get(field, ""))
        if current not in allowed_from:
            return (
                False,
                current,
                current,
                f"{label} {entity_id} is {current}; action requires "
                f"{' or '.join(sorted(allowed_from))}",
            )

        entity[field] = new_value
        return True, current, new_value, f"{label} {entity_id} changed from {current} to {new_value}"


def apply_change(
    env: SimulatedEnvironment,
    *,
    action: str,
    label: str,
    entity_type: str,
    target_id: str | None,
    allowed_from: set[str] | frozenset[str],
    new_value: str,
    field: str = "status",
) -> ExecutionResult:
    """Shared helper used by every simulated action module."""
    ok, before, after, reason = env.transition(
        entity_type, target_id, new_value, allowed_from, field=field
    )
    return ExecutionResult(
        action=action,
        label=label,
        target_type=entity_type,
        target_id=target_id,
        success=ok,
        message=reason,
        before=f"{field}={before}" if before else "",
        after=f"{field}={after}" if ok else "",
    )
