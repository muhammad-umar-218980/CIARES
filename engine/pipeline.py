"""
The end-to-end investigation pipeline.

This is the single function the Streamlit portal and the tests call:

    observations -> working memory -> forward chaining -> diagnosis
                 -> decision engine -> Investigation

Keeping the pipeline here (instead of inside ``app.py``) means the exact same
reasoning runs for a manual investigation, a predefined scenario and a pytest
case.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Sequence

from config import THRESHOLDS  # noqa: F401  (re-exported for convenience)
from knowledge_base.rule_registry import ALL_RULES

from .decision_engine import DecisionEngine
from .inference_engine import InferenceEngine, InferenceResult
from .models import Finding, Investigation, RuleActivation, Severity
from .working_memory import WorkingMemory


def build_findings(activations: Sequence[RuleActivation]) -> list[Finding]:
    """
    Turn fired rules into findings.

    One conclusion = one finding. If several rules derive the same conclusion
    they are merged, the strongest severity wins and every supporting rule id is
    preserved - findings are never discarded because another one outranks them.
    """
    findings: dict[str, Finding] = {}
    for activation in activations:
        rule = activation.rule
        existing = findings.get(rule.conclusion_key)
        if existing is None:
            findings[rule.conclusion_key] = Finding(
                key=rule.conclusion_key,
                label=rule.conclusion_label,
                severity=rule.severity,
                module=rule.module,
                rule_ids=[rule.id],
                supporting_facts=tuple(rule.condition_fields),
                sequence=activation.sequence,
                description=rule.description,
                recommended_action=rule.recommended_action,
                action_phase=rule.action_phase,
            )
            continue

        if rule.id not in existing.rule_ids:
            existing.rule_ids.append(rule.id)
        if rule.severity.rank > existing.severity.rank:
            existing.severity = rule.severity
        existing.supporting_facts = tuple(
            dict.fromkeys(existing.supporting_facts + rule.condition_fields)
        )
        if existing.recommended_action is None and rule.recommended_action:
            existing.recommended_action = rule.recommended_action
            existing.action_phase = rule.action_phase

    return sorted(findings.values(), key=lambda finding: (-finding.severity.rank, finding.sequence))


def run_investigation(
    observations: dict[str, Any],
    name: str = "Untitled Investigation",
    rules: Sequence = ALL_RULES,
    scenario_id: str | None = None,
    investigation_id: str | None = None,
    decision_engine: DecisionEngine | None = None,
) -> Investigation:
    investigation = Investigation(
        id=investigation_id or _new_investigation_id(),
        name=name,
        started_at=datetime.now().isoformat(timespec="seconds"),
        observations={key: value for key, value in observations.items() if value is not None},
        scenario_id=scenario_id,
    )

    memory = WorkingMemory()
    memory.add_observations(observations)

    inference = InferenceEngine(rules)
    result: InferenceResult = inference.run(memory)

    findings = build_findings(result.activations)
    memory.record_trace(
        "diagnosis",
        f"{len(findings)} finding(s) derived from {result.activation_count} rule activation(s)",
    )

    engine = decision_engine or DecisionEngine()
    actions = engine.decide(findings, investigation_id=investigation.id)
    deferred = sum(1 for action in actions if action.deferred)
    memory.record_trace(
        "decision",
        f"{len(actions)} recommendation(s) produced, {deferred} deferred",
    )

    investigation.activations = list(result.activations)
    investigation.findings = findings
    investigation.actions = actions
    investigation.trace = list(memory.trace)
    investigation.terminated_reason = result.terminated_reason
    investigation.inference_cycles = result.cycles
    investigation.memory = memory
    return investigation


def _new_investigation_id() -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = uuid.uuid4().hex[:4].upper()
    return f"INV-{stamp}-{suffix}"


def severity_totals(investigations: Sequence[dict[str, Any] | Investigation]) -> dict[str, int]:
    """Aggregate severity counts for the Security Overview page."""
    totals = {severity.value: 0 for severity in Severity}
    for item in investigations:
        if isinstance(item, Investigation):
            counts = item.severity_counts
        else:
            counts = item.get("severity_counts", {})
        for severity, count in counts.items():
            totals[severity] = totals.get(severity, 0) + int(count)
    return totals
