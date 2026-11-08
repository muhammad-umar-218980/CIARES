"""
Working Memory - the facts of *this* investigation.

The Knowledge Base is general cybersecurity knowledge and lives forever; the
Working Memory is created per investigation and holds only what is true of the
current incident. Facts have three states:

    True     - a confirmed observation or a derived conclusion
    False    - explicitly observed to be absent
    Unknown  - never provided (the key is absent, or stored as None)

Unknown is deliberately different from False: a rule that needs
``unusual_login_location is True`` must not fire just because nobody asked.
"""

from __future__ import annotations

from typing import Any

from .models import (
    ConditionEvaluation,
    Fact,
    Rule,
    RuleActivation,
    values_equal,
)


class ContradictionError(ValueError):
    """Raised when two different values are asserted for the same fact."""


class WorkingMemory:
    def __init__(self, entities: dict[str, str] | None = None) -> None:
        self.entities: dict[str, str] = dict(entities or {})
        self._facts: dict[str, Fact] = {}
        self._sequence = 0
        self.trace: list[dict[str, Any]] = []

    # -- observations -------------------------------------------------------
    def add_observation(self, key: str, value: Any) -> Fact:
        """
        Record a user-supplied observation.

        ``None`` is stored as an explicit Unknown fact so the trace can show
        that the field was considered but not provided.
        """
        existing = self._facts.get(key)
        if existing is not None and existing.derived:
            raise ContradictionError(
                f"{key!r} was derived by {existing.rule_id} and cannot be "
                f"overwritten by an observation"
            )
        if (
            existing is not None
            and existing.value is not None
            and value is not None
            and not values_equal(existing.value, value)
        ):
            raise ContradictionError(
                f"Contradictory observation for {key!r}: "
                f"{existing.value!r} then {value!r}"
            )

        self._sequence += 1
        fact = Fact(
            key=key,
            value=value,
            source="Observation",
            sequence=self._sequence,
            derived=False,
        )
        self._facts[key] = fact
        self.record_trace(
            "observation",
            f"Observation recorded: {key} = {fact.state}",
            key=key,
        )
        return fact

    def add_observations(self, observations: dict[str, Any]) -> None:
        for key, value in observations.items():
            self.add_observation(key, value)

    # -- inference ----------------------------------------------------------
    def infer(
        self,
        key: str,
        value: Any,
        rule: Rule,
        supporting: dict[str, Any],
    ) -> bool:
        """
        Insert a conclusion derived by ``rule``.

        Returns True when the fact is new. Returns False when the same value was
        already established (the activation is still recorded, but no duplicate
        fact is created). Raises on a genuine contradiction so a fact is never
        silently overwritten.
        """
        existing = self._facts.get(key)
        if existing is not None and existing.value is not None:
            if not values_equal(existing.value, value):
                raise ContradictionError(
                    f"Rule {rule.id} tried to set {key!r} = {value!r} but "
                    f"working memory already holds {existing.value!r}"
                )
            return False

        self._sequence += 1
        self._facts[key] = Fact(
            key=key,
            value=value,
            source=rule.id,
            sequence=self._sequence,
            derived=True,
            rule_id=rule.id,
            supporting=tuple(supporting.items()),
        )
        return True

    def record_activation(
        self,
        rule: Rule,
        evaluations: tuple[ConditionEvaluation, ...],
        activation_key: str,
        inserted_new_fact: bool,
        sequence: int,
    ) -> RuleActivation:
        activation = RuleActivation(
            sequence=sequence,
            rule=rule,
            evaluations=evaluations,
            entities=dict(self.entities),
            conclusion_key=rule.conclusion_key,
            conclusion_label=rule.conclusion_label,
            conclusion_value=True,
            activation_key=activation_key,
            inserted_new_fact=inserted_new_fact,
        )
        self.record_trace(
            "activation",
            f"{rule.id} {rule.name} activated -> {rule.conclusion_label}",
            rule_id=rule.id,
            conclusion=rule.conclusion_key,
            inserted_new_fact=inserted_new_fact,
        )
        return activation

    # -- reading ------------------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        fact = self._facts.get(key)
        return default if fact is None or fact.value is None else fact.value

    def get_fact(self, key: str) -> Fact | None:
        return self._facts.get(key)

    def is_known(self, key: str) -> bool:
        fact = self._facts.get(key)
        return fact is not None and fact.value is not None

    def state(self, key: str) -> str:
        fact = self._facts.get(key)
        return fact.state if fact is not None else "Unknown"

    def all_facts(self) -> list[Fact]:
        return sorted(self._facts.values(), key=lambda fact: fact.sequence)

    def derived_facts(self) -> list[Fact]:
        return [fact for fact in self.all_facts() if fact.derived]

    def observations(self) -> list[Fact]:
        return [fact for fact in self.all_facts() if not fact.derived]

    def as_dict(self, include_unknown: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, fact in self._facts.items():
            if fact.value is None and not include_unknown:
                continue
            result[key] = fact.value
        return result

    def provenance(self, key: str) -> dict[str, Any]:
        fact = self._facts.get(key)
        if fact is None:
            return {"key": key, "state": "Unknown", "source": "not established"}
        return {
            "key": key,
            "state": fact.state,
            "source": fact.source,
            "derived": fact.derived,
            "rule_id": fact.rule_id,
            "supporting": dict(fact.supporting),
        }

    # -- trace --------------------------------------------------------------
    def record_trace(self, kind: str, message: str, **detail: Any) -> None:
        self.trace.append(
            {
                "step": len(self.trace) + 1,
                "kind": kind,
                "message": message,
                **detail,
            }
        )
