"""
The Report Writer.

CIARES does not show the analyst a wall of rule identifiers. This module turns
an :class:`Investigation` into the sentences that the public portal displays:

* a headline and a threat score with a one-line severity sentence,
* a plain-language description of every finding,
* "what led to this" - the observations that satisfied each rule, with no rule
  identifiers in the text,
* the recommended response, and
* after human approval, a numbered response plan.

Rule identifiers remain available to administrators through the evidence table
and the admin portal; they are never part of the public narrative.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .decision_engine import ACTION_LIBRARY
from .models import Investigation, ResponseAction, Severity

# Documented CIARES project assumption: the score is additive and deterministic,
# never probabilistic. The cap keeps the meter inside 0-100.
SEVERITY_POINTS: dict[Severity, int] = {
    Severity.CRITICAL: 50,
    Severity.HIGH: 25,
    Severity.MEDIUM: 10,
    Severity.LOW: 5,
}
MAX_THREAT_SCORE = 100

SEVERITY_SENTENCE: dict[Severity, str] = {
    Severity.CRITICAL: (
        "the evidence is conclusive or the activity is still in progress, so "
        "containment should begin immediately"
    ),
    Severity.HIGH: (
        "the evidence is strong and the situation should be contained during this "
        "working day"
    ),
    Severity.MEDIUM: (
        "the evidence is suggestive, so it should be verified before disruptive "
        "action is taken"
    ),
    Severity.LOW: (
        "the evidence is weak, so monitoring and further collection are appropriate"
    ),
}


# ---------------------------------------------------------------------------
# Headline, score and overview
# ---------------------------------------------------------------------------
def threat_score(investigation: Investigation) -> int:
    score = sum(SEVERITY_POINTS[finding.severity] for finding in investigation.findings)
    return min(score, MAX_THREAT_SCORE)


def top_severity(investigation: Investigation) -> Severity | None:
    if not investigation.findings:
        return None
    return max((finding.severity for finding in investigation.findings), key=lambda s: s.rank)


def headline(investigation: Investigation) -> str:
    if not investigation.findings:
        return "No incident detected"
    return investigation.findings[0].label


def threat_sentence(investigation: Investigation) -> str:
    score = threat_score(investigation)
    severity = top_severity(investigation)
    if severity is None:
        return (
            "Threat level 0 out of 100 - no finding was derived from the information "
            "supplied, so no response is recommended."
        )
    return (
        f"Threat level {score} out of 100 - {severity.value} severity: "
        f"{SEVERITY_SENTENCE[severity]}."
    )


def overview_paragraph(investigation: Investigation) -> str:
    scores = investigation.severity_counts
    findings = len(investigation.findings)
    observations = len(investigation.observations)

    if findings == 0:
        return (
            f"CIARES examined {observations} observation(s) and could not derive a "
            "finding. Either the incident is not present in the supplied evidence, or "
            "an important observation is missing."
        )

    parts = [
        f"CIARES examined {observations} observation(s) and derived {findings} finding(s): "
        f"{scores['Critical']} critical, {scores['High']} high, "
        f"{scores['Medium']} medium and {scores['Low']} low."
    ]
    worst = investigation.findings[0]
    parts.append(
        f"The most serious conclusion is {worst.label.lower()}, rated "
        f"{worst.severity.value.lower()} severity. {worst.description}"
    )
    return " ".join(parts)


def finding_paragraphs(investigation: Investigation) -> list[dict[str, str]]:
    """One plain-language paragraph per finding, ordered by severity."""
    return [
        {
            "title": finding.label,
            "severity": finding.severity.value,
            "text": finding.description,
        }
        for finding in investigation.findings
    ]


# ---------------------------------------------------------------------------
# Reasoning ("what led to this")
# ---------------------------------------------------------------------------
def _observed_phrase(evaluation: Any) -> str:
    condition = evaluation.condition
    text = condition.describe()
    value = evaluation.observed
    if isinstance(value, bool) or value is None:
        return text
    return f"{text} (observed {value})"


def reasoning_paragraphs(investigation: Investigation) -> list[str]:
    """
    Explain each conclusion using the conditions that were satisfied.

    The rule identifiers are deliberately omitted: the public portal explains the
    reasoning in the analyst's language, while ``/admin`` keeps the trace.
    """
    paragraphs: list[str] = []
    seen: set[str] = set()

    for activation in investigation.activations:
        conclusion = activation.conclusion_label
        if conclusion in seen:
            continue
        seen.add(conclusion)

        phrases = [_observed_phrase(evaluation) for evaluation in activation.evaluations]
        if not phrases:
            continue
        if len(phrases) == 1:
            evidence = phrases[0]
        else:
            evidence = ", ".join(phrases[:-1]) + " and " + phrases[-1]
        paragraphs.append(
            f"{conclusion} is supported by the following observations: {evidence}."
        )

    if not paragraphs:
        paragraphs.append(
            "No rule was satisfied, so there is no reasoning chain to report. Add the "
            "missing observations and run the investigation again."
        )
    return paragraphs


def friendly_time(value: str) -> str:
    """Render a stored ISO timestamp as ``13 Nov 2026 at 02:19``."""
    for pattern in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, pattern).strftime("%d %b %Y at %H:%M")
        except (TypeError, ValueError):
            continue
    return value or "unknown time"


def evidence_rows(investigation: Investigation) -> list[dict[str, Any]]:
    """Administrative evidence table: one row per rule activation."""
    return [
        {
            "Rule": activation.rule.id,
            "Rule name": activation.rule.name,
            "Conclusion": activation.conclusion_label,
            "Severity": activation.rule.severity.value,
        }
        for activation in investigation.activations
    ]


# ---------------------------------------------------------------------------
# Recommendations and approval
# ---------------------------------------------------------------------------
def recommendation_sentence(action: ResponseAction) -> str:
    spec = ACTION_LIBRARY.get(action.action)
    detail = spec.description if spec else ""
    sentence = f"{action.label} ({action.phase.value.lower()} phase)."
    return f"{sentence} {detail}".strip()


def actionable_recommendations(investigation: Investigation) -> list[ResponseAction]:
    return [action for action in investigation.actions if not action.deferred]


def deferred_recommendations(investigation: Investigation) -> list[ResponseAction]:
    return [action for action in investigation.actions if action.deferred]


def approve(investigation: Investigation, action_ids: list[str]) -> list[ResponseAction]:
    """Record the analyst's decision. Approval is the hand-over point to a human."""
    selected = set(action_ids)
    for action in investigation.actions:
        action.approved = action.action_id in selected and not action.deferred
    if investigation.approved_actions:
        investigation.approved_at = datetime.now().isoformat(timespec="minutes")
    else:
        investigation.approved_at = ""
    return investigation.approved_actions


def plan_steps(investigation: Investigation) -> list[str]:
    """Imperative steps built from the approved recommendations."""
    steps: list[str] = []
    for action in investigation.approved_actions:
        spec = ACTION_LIBRARY.get(action.action)
        detail = spec.description if spec else ""
        steps.append(f"{action.label}. {detail}".strip())
    return steps


def plan_text(investigation: Investigation) -> str:
    """Plain-text response plan for the download button."""
    lines = [
        "CIARES RESPONSE PLAN",
        "=" * 70,
        f"Investigation : {investigation.name}",
        f"Reference     : {investigation.id}",
        f"Approved at   : "
        f"{friendly_time(investigation.approved_at) if investigation.approved_at else 'not approved'}",
        "",
        "DIAGNOSIS",
        "-" * 70,
        headline(investigation),
        threat_sentence(investigation),
        "",
        overview_paragraph(investigation),
        "",
    ]
    for paragraph in reasoning_paragraphs(investigation):
        lines.extend([paragraph, ""])

    steps = plan_steps(investigation)
    lines.extend(["APPROVED RESPONSE", "-" * 70])
    if steps:
        lines.extend(f"{index}. {step}" for index, step in enumerate(steps, start=1))
    else:
        lines.append("No response action has been approved.")

    deferred = deferred_recommendations(investigation)
    if deferred:
        lines.extend(["", "DEFERRED UNTIL CONTAINMENT IS VERIFIED", "-" * 70])
        lines.extend(f"- {action.label}: {action.defer_reason}" for action in deferred)

    lines.extend(
        [
            "",
            "-" * 70,
            "CIARES is a decision-support Expert System. It does not execute any",
            "action; the approved plan is carried out by the responsible analyst.",
        ]
    )
    return "\n".join(lines)
