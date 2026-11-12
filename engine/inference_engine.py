"""
The Forward-Chaining Inference Engine.

Algorithm (one cycle = one rule firing):

    1. Evaluate every rule against working memory.
    2. A rule is ELIGIBLE only when every one of its conditions is satisfied.
       A condition that is Unknown makes the rule ineligible (never "assume").
    3. Build an activation key from rule id + the exact supporting facts, and
       discard any key that already fired.
    4. Fire the highest-priority eligible rule, insert its conclusion and
       record the activation.
    5. Repeat from step 1 until no eligible activation remains (fixed point).

Firing one rule at a time and re-evaluating is slightly more work than a batch
loop, but it guarantees the recorded activation order is the real reasoning
order, which is exactly what the Explanation Facility needs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

from .models import ConditionEvaluation, Rule, RuleActivation
from .working_memory import WorkingMemory


@dataclass
class InferenceResult:
    activations: list[RuleActivation] = field(default_factory=list)
    cycles: int = 0
    terminated_reason: str = "completed"
    fired_rule_ids: set[str] = field(default_factory=set)

    @property
    def activation_count(self) -> int:
        return len(self.activations)


class InferenceEngine:
    def __init__(self, rules: Sequence[Rule], max_cycles: int | None = None) -> None:
        self.rules: tuple[Rule, ...] = tuple(rules)
        self.max_cycles = max_cycles or max(100, len(self.rules) * 5)

    # -- rule evaluation ----------------------------------------------------
    def evaluate_rule(
        self, rule: Rule, memory: WorkingMemory
    ) -> tuple[bool, tuple[ConditionEvaluation, ...]]:
        """Return (eligible, evaluations). Unknown or False => not eligible."""
        evaluations: list[ConditionEvaluation] = []
        eligible = True
        for condition in rule.conditions:
            known = memory.is_known(condition.field)
            observed = memory.get(condition.field)
            satisfied, note = condition.evaluate(observed, known)
            evaluations.append(
                ConditionEvaluation(
                    condition=condition,
                    known=known,
                    observed=observed,
                    satisfied=satisfied,
                    note=note,
                )
            )
            if satisfied is not True:
                eligible = False
        return eligible, tuple(evaluations)

    # -- activation tracking ------------------------------------------------
    @staticmethod
    def activation_key(
        rule: Rule,
        evaluations: Iterable[ConditionEvaluation],
    ) -> str:
        """
        Rule id + the exact supporting fact combination.

        This is why a rule cannot fire twice against the same observations, while
        still being allowed to fire again when the supporting facts change.
        """
        support_part = "|".join(
            f"{evaluation.condition.field}={evaluation.observed!r}"
            for evaluation in evaluations
        )
        return f"{rule.id}::{support_part}"

    def eligible_activations(
        self, memory: WorkingMemory, fired: set[str]
    ) -> list[tuple[Rule, tuple[ConditionEvaluation, ...], str]]:
        eligible: list[tuple[Rule, tuple[ConditionEvaluation, ...], str]] = []
        for rule in self.rules:
            is_eligible, evaluations = self.evaluate_rule(rule, memory)
            if not is_eligible:
                continue
            key = self.activation_key(rule, evaluations)
            if key in fired:
                continue
            eligible.append((rule, evaluations, key))
        # Deterministic conflict resolution: strongest finding first, then the
        # author-declared priority, then rule id for stability.
        eligible.sort(key=lambda item: (-item[0].severity.rank, item[0].priority, item[0].id))
        return eligible

    # -- main loop ----------------------------------------------------------
    def run(self, memory: WorkingMemory) -> InferenceResult:
        result = InferenceResult()
        fired: set[str] = set()
        memory.record_trace(
            "start",
            f"Inference started with {len(self.rules)} rules and "
            f"{len(memory.observations())} observations",
        )

        while result.cycles < self.max_cycles:
            eligible = self.eligible_activations(memory, fired)
            if not eligible:
                result.terminated_reason = "fixed point: no further eligible rules"
                break

            rule, evaluations, key = eligible[0]
            inserted = memory.infer(
                rule.conclusion_key,
                True,
                rule,
                {
                    evaluation.condition.field: evaluation.observed
                    for evaluation in evaluations
                },
            )
            fired.add(key)
            result.cycles += 1
            activation = memory.record_activation(
                rule=rule,
                evaluations=evaluations,
                activation_key=key,
                inserted_new_fact=inserted,
                sequence=len(result.activations) + 1,
            )
            result.activations.append(activation)
            result.fired_rule_ids.add(rule.id)
        else:
            result.terminated_reason = "cycle limit reached"

        memory.record_trace(
            "finish",
            f"Inference finished after {result.activation_count} activations: "
            f"{result.terminated_reason}",
        )
        return result

    # -- convenience --------------------------------------------------------
    def rules_for_conclusion(self, conclusion_key: str) -> list[Rule]:
        return [rule for rule in self.rules if rule.conclusion_key == conclusion_key]

    def supports(self, conclusion_key: str) -> bool:
        return any(rule.conclusion_key == conclusion_key for rule in self.rules)
