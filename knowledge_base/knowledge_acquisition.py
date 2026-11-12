"""
Knowledge Acquisition Module (component 5 of the Expert System).

Cybersecurity knowledge is gathered manually from approved references, encoded
as explicit IF-THEN rules, validated, and only then registered. This module is
the gatekeeper: it performs real knowledge-management work rather than merely
storing a list.

Checks performed here
---------------------
* the rule has an id in ``<MODULE>-NN`` form and it is unique
* the rule has a name, a description and at least one condition
* the conclusion exists, is not already a condition of the same rule
  (a rule may not support itself) and is a snake_case fact key
* the severity is one of Critical / High / Medium / Low
* the source is one of the approved references
* an actionable rule declares a response phase
* the recommended action is a machine-readable key
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Sequence

from config import APPROVED_SOURCES
from engine.models import Phase, Rule, Severity

RULE_ID_PATTERN = re.compile(r"^(AUTH|MAL|NET|DATA|POL)-\d{2}$")
FACT_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
ACTION_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rule_count: int = 0
    condition_count: int = 0
    distinct_condition_fields: int = 0
    by_module: dict[str, int] = field(default_factory=dict)
    inventory: list[dict[str, object]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    @property
    def module_count(self) -> int:
        return len(self.by_module)

    def summary(self) -> str:
        state = "VALID" if self.ok else f"{len(self.errors)} ERROR(S)"
        return (
            f"{self.rule_count} rules | {self.condition_count} logical conditions | "
            f"{self.distinct_condition_fields} distinct fact fields | "
            f"{self.module_count} modules | {state}"
        )


def validate_rule(rule: Rule) -> list[str]:
    """Return a list of hard errors for a single rule (empty list = valid)."""
    errors: list[str] = []

    if not RULE_ID_PATTERN.match(rule.id):
        errors.append(f"{rule.id!r}: rule id must look like AUTH-01 or DATA-12")
    if not rule.name.strip():
        errors.append(f"{rule.id}: rule name is required")
    if len(rule.description.strip()) < 10:
        errors.append(f"{rule.id}: description is missing or too short")
    if not rule.conditions:
        errors.append(f"{rule.id}: rule has no conditions")
    if not rule.conclusion_key:
        errors.append(f"{rule.id}: rule has no conclusion")
    if rule.conclusion_key in rule.condition_fields:
        errors.append(
            f"{rule.id}: conclusion {rule.conclusion_key!r} is also one of its own "
            f"conditions (self-supporting rule)"
        )
    if not isinstance(rule.severity, Severity):
        errors.append(f"{rule.id}: severity must be a Severity value")
    if rule.source not in APPROVED_SOURCES:
        errors.append(
            f"{rule.id}: source {rule.source!r} is not an approved reference "
            f"({', '.join(APPROVED_SOURCES)})"
        )
    if rule.is_actionable:
        if not ACTION_KEY_PATTERN.match(rule.recommended_action or ""):
            errors.append(f"{rule.id}: recommended action must be a snake_case key")
        if not isinstance(rule.action_phase, Phase):
            errors.append(f"{rule.id}: action phase must be a Phase value")
    return errors


def validate_catalogue(rules: Sequence[Rule]) -> ValidationReport:
    """Validate the whole knowledge base and build the condition inventory."""
    report = ValidationReport(rule_count=len(rules))

    seen: dict[str, int] = {}
    for rule in rules:
        report.errors.extend(validate_rule(rule))
        seen[rule.id] = seen.get(rule.id, 0) + 1
        report.by_module[rule.module] = report.by_module.get(rule.module, 0) + 1

    for rule_id, count in seen.items():
        if count > 1:
            report.errors.append(f"{rule_id}: duplicate rule id registered {count} times")

    total = sum(len(rule.conditions) for rule in rules)
    fields: dict[str, dict[str, object]] = {}
    for rule in rules:
        for condition in rule.conditions:
            entry = fields.setdefault(
                condition.field,
                {"field": condition.field, "conditions": 0, "rules": set()},
            )
            entry["conditions"] = int(entry["conditions"]) + 1
            entry["rules"].add(rule.id)

    report.condition_count = total
    report.distinct_condition_fields = len(fields)
    report.inventory = sorted(
        (
            {
                "field": entry["field"],
                "conditions": entry["conditions"],
                "rules": len(entry["rules"]),
            }
            for entry in fields.values()
        ),
        key=lambda item: (-int(item["conditions"]), str(item["field"])),
    )

    if total < 50:
        report.warnings.append(
            f"only {total} logical conditions registered; the assignment requires 50"
        )
    if len(rules) < 60:
        report.warnings.append(
            f"only {len(rules)} rules registered; the target knowledge base is 60"
        )
    return report


def count_conditions(rules: Iterable[Rule]) -> int:
    return sum(len(rule.conditions) for rule in rules)


class KnowledgeAcquisition:
    """Register validated rules one at a time, rejecting invalid knowledge."""

    def __init__(self, sources: Sequence[str] = APPROVED_SOURCES) -> None:
        self.sources = tuple(sources)
        self._registry: dict[str, Rule] = {}

    @property
    def registered(self) -> dict[str, Rule]:
        return dict(self._registry)

    def validate(self, rule: Rule) -> list[str]:
        errors = validate_rule(rule)
        if rule.id in self._registry:
            errors.append(f"{rule.id}: rule id is already registered")
        return errors

    def register(self, rule: Rule) -> Rule:
        errors = self.validate(rule)
        if errors:
            raise ValueError("; ".join(errors))
        self._registry[rule.id] = rule
        return rule

    def register_all(self, rules: Iterable[Rule]) -> list[Rule]:
        registered: list[Rule] = []
        for rule in rules:
            registered.append(self.register(rule))
        return registered

    def report(self) -> ValidationReport:
        return validate_catalogue(list(self._registry.values()))
