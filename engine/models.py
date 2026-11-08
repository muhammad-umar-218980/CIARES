"""
Standard data structures used throughout CIARES.

The Expert System components must communicate using consistent objects, so
everything (rules, facts, findings, actions, executions) is defined here and
imported everywhere else. No logic lives in this module - it is pure structure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Controlled vocabularies
# ---------------------------------------------------------------------------
class Severity(str, Enum):
    """Finding severity. Rank is used for ordering, never for discarding."""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

    @property
    def rank(self) -> int:
        return {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}[self.value]

    def __str__(self) -> str:  # keeps tables readable
        return self.value


class Phase(str, Enum):
    """Response phase, following the containment/eradication/recovery model."""

    CONTAINMENT = "Containment"
    ERADICATION = "Eradication"
    RECOVERY = "Recovery"
    ESCALATION = "Escalation"

    @property
    def order(self) -> int:
        return {
            "Containment": 1,
            "Eradication": 2,
            "Recovery": 3,
            "Escalation": 4,
        }[self.value]

    def __str__(self) -> str:
        return self.value


# Supported condition operators. A rule condition is a declarative triple
# (field, operator, value) so it can be printed, validated and explained.
OPERATORS: frozenset[str] = frozenset(
    {"==", "!=", ">", ">=", "<", "<=", "in", "not in"}
)


def _is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def values_equal(observed: Any, expected: Any) -> bool:
    """Equality that does not let ``True == 1`` blur booleans and numbers."""
    if _is_bool(observed) or _is_bool(expected):
        return _is_bool(observed) and _is_bool(expected) and observed == expected
    return observed == expected


@dataclass(frozen=True)
class Condition:
    """
    One logical condition inside an IF-THEN rule, e.g. failed_login_attempts >= 10.

    ``label`` is the human wording used by the Explanation Facility; when it is
    empty the condition describes itself.
    """

    field: str
    operator: str
    value: Any = True
    label: str = ""

    def __post_init__(self) -> None:
        if self.operator not in OPERATORS:
            raise ValueError(
                f"Unsupported operator {self.operator!r} in condition on {self.field!r}"
            )

    def describe(self) -> str:
        if self.label:
            return self.label
        if self.operator == "==" and _is_bool(self.value):
            return f"{self.field} is {self.value}"
        return f"{self.field} {self.operator} {self.value}"

    def evaluate(self, observed: Any, known: bool) -> tuple[bool | None, str]:
        """
        Three-valued evaluation.

        Returns (True, note), (False, note) or (None, note) where None means
        "cannot decide because the fact is Unknown". A rule containing an
        undecidable condition is not eligible to fire.
        """
        if not known:
            return None, f"{self.field} is Unknown - condition cannot be evaluated"

        op = self.operator
        expected = self.value

        if op in {">", ">=", "<", "<="}:
            if not (_is_number(observed) and _is_number(expected)):
                return None, (
                    f"{self.field} = {observed!r} is not numeric - "
                    f"cannot evaluate {op}"
                )
            satisfied = {
                ">": observed > expected,
                ">=": observed >= expected,
                "<": observed < expected,
                "<=": observed <= expected,
            }[op]
        elif op == "==":
            satisfied = values_equal(observed, expected)
        elif op == "!=":
            satisfied = not values_equal(observed, expected)
        elif op == "in":
            try:
                satisfied = observed in expected
            except TypeError:
                return None, f"{self.field} = {observed!r} is not comparable with {expected!r}"
        else:  # "not in"
            try:
                satisfied = observed not in expected
            except TypeError:
                return None, f"{self.field} = {observed!r} is not comparable with {expected!r}"

        verdict = "satisfied" if satisfied else "not satisfied"
        return satisfied, f"Observed {observed!r} -> {self.describe()} -> {verdict}"


@dataclass(frozen=True)
class Rule:
    """
    A single manually authored IF-THEN rule.

    A rule is a *diagnostic* rule when it derives an indicator and an
    *actionable* rule when it also recommends a response. Only rules with a
    ``recommended_action`` can create a response action; every rule still
    produces a finding.
    """

    id: str
    name: str
    module: str
    description: str
    conditions: tuple[Condition, ...]
    conclusion_key: str
    conclusion_label: str
    severity: Severity
    source: str
    recommended_action: str | None = None
    action_phase: Phase = Phase.ESCALATION
    entity_type: str | None = None
    priority: int = 100
    tags: tuple[str, ...] = ()

    @property
    def condition_count(self) -> int:
        return len(self.conditions)

    @property
    def condition_fields(self) -> tuple[str, ...]:
        return tuple(condition.field for condition in self.conditions)

    @property
    def is_actionable(self) -> bool:
        return self.recommended_action is not None

    def describe_conditions(self) -> str:
        return " AND ".join(condition.describe() for condition in self.conditions)


@dataclass
class Fact:
    """A single entry in working memory, with provenance for explanations."""

    key: str
    value: Any
    source: str
    sequence: int = 0
    derived: bool = False
    rule_id: str | None = None
    supporting: tuple[tuple[str, Any], ...] = ()

    @property
    def known(self) -> bool:
        return self.value is not None

    @property
    def state(self) -> str:
        if not self.known:
            return "Unknown"
        if _is_bool(self.value):
            return "True" if self.value else "False"
        return str(self.value)


@dataclass(frozen=True)
class ConditionEvaluation:
    """The result of evaluating one condition against working memory."""

    condition: Condition
    known: bool
    observed: Any
    satisfied: bool | None
    note: str

    @property
    def status(self) -> str:
        if self.satisfied is None:
            return "Unknown"
        return "Satisfied" if self.satisfied else "Not satisfied"


@dataclass
class RuleActivation:
    """A rule that has fired, with everything needed to justify it later."""

    sequence: int
    rule: Rule
    evaluations: tuple[ConditionEvaluation, ...]
    entities: dict[str, str]
    conclusion_key: str
    conclusion_label: str
    conclusion_value: Any
    activation_key: str
    inserted_new_fact: bool = True
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


@dataclass
class Finding:
    """A diagnosed cybersecurity issue, supported by one or more rule firings."""

    key: str
    label: str
    severity: Severity
    module: str
    rule_ids: list[str] = field(default_factory=list)
    supporting_facts: tuple[str, ...] = ()
    sequence: int = 0
    description: str = ""
    recommended_action: str | None = None
    action_phase: Phase = Phase.ESCALATION
    entity_type: str | None = None


@dataclass
class ExecutionResult:
    """Outcome of one simulated action against the simulated environment."""

    action: str
    label: str
    target_type: str
    target_id: str | None
    success: bool
    message: str
    before: str = ""
    after: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    @property
    def status(self) -> str:
        return "Success" if self.success else "Rejected"


@dataclass
class ResponseAction:
    """An action proposed by the Decision Engine for a specific finding."""

    action: str
    label: str
    phase: Phase
    priority: int
    target_type: str
    target_id: str | None
    finding_key: str
    finding_label: str
    finding_severity: Severity
    reason: str
    executable: bool = True
    blocked_reason: str = ""
    status: str = "Proposed"  # Proposed | Executed | Rejected | Skipped
    execution: ExecutionResult | None = None
    action_id: str = ""

    @property
    def target(self) -> str:
        return self.target_id or "(no target)"


@dataclass
class Investigation:
    """A complete investigation: inputs, reasoning, findings and responses."""

    id: str
    name: str
    started_at: str
    observations: dict[str, Any]
    entities: dict[str, str] = field(default_factory=dict)
    activations: list[RuleActivation] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    actions: list[ResponseAction] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)
    terminated_reason: str = "completed"
    inference_cycles: int = 0
    scenario_id: str | None = None
    environment: Any = None  # SimulatedEnvironment, excluded from JSON records

    @property
    def severity_counts(self) -> dict[str, int]:
        counts = {severity.value: 0 for severity in Severity}
        for finding in self.findings:
            counts[finding.severity.value] += 1
        return counts

    @property
    def executed_actions(self) -> list[ResponseAction]:
        return [action for action in self.actions if action.execution is not None]

    def to_record(self) -> dict[str, Any]:
        """JSON-safe summary used by the Investigation History page."""
        return {
            "id": self.id,
            "name": self.name,
            "started_at": self.started_at,
            "scenario_id": self.scenario_id,
            "observations": {k: v for k, v in self.observations.items()},
            "entities": dict(self.entities),
            "findings": [
                {
                    "key": finding.key,
                    "label": finding.label,
                    "severity": finding.severity.value,
                    "module": finding.module,
                    "rule_ids": list(finding.rule_ids),
                }
                for finding in self.findings
            ],
            "activations": [
                {
                    "sequence": activation.sequence,
                    "rule_id": activation.rule.id,
                    "rule_name": activation.rule.name,
                    "conclusion": activation.conclusion_key,
                    "conclusion_label": activation.conclusion_label,
                }
                for activation in self.activations
            ],
            "actions": [
                {
                    "action": action.action,
                    "label": action.label,
                    "target_type": action.target_type,
                    "target_id": action.target_id,
                    "status": action.status,
                    "execution": None
                    if action.execution is None
                    else {
                        "success": action.execution.success,
                        "message": action.execution.message,
                        "before": action.execution.before,
                        "after": action.execution.after,
                    },
                }
                for action in self.actions
            ],
            "severity_counts": self.severity_counts,
            "terminated_reason": self.terminated_reason,
        }
