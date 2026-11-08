"""
The Explanation Facility.

Two kinds of explanation are produced, matching the lecture material:

* Trace explanation       - the ordered sequence of rule activations and the
                            conclusions they produced.
* Justification explanation - for a single activation, every condition with the
                            observed value, whether it was satisfied, and, for
                            actions, why the action was chosen and what happened
                            when it was executed.

Nothing here re-runs the engine; it only interprets the records that the engine,
the decision engine and the simulation already produced.
"""

from __future__ import annotations

from typing import Any

from .models import Investigation, ResponseAction, RuleActivation


class ExplanationEngine:
    # -- trace --------------------------------------------------------------
    @staticmethod
    def trace_rows(investigation: Investigation) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for step in investigation.trace:
            rows.append(
                {
                    "Step": step["step"],
                    "Event": step["kind"].title(),
                    "Detail": step["message"],
                }
            )
        return rows

    @staticmethod
    def activation_rows(investigation: Investigation) -> list[dict[str, Any]]:
        return [
            {
                "#": activation.sequence,
                "Rule": activation.rule.id,
                "Name": activation.rule.name,
                "Module": activation.rule.module,
                "Conclusion": activation.conclusion_label,
                "Severity": activation.rule.severity.value,
                "New fact": "Yes" if activation.inserted_new_fact else "Already known",
            }
            for activation in investigation.activations
        ]

    # -- justification ------------------------------------------------------
    @staticmethod
    def justification(activation: RuleActivation) -> dict[str, Any]:
        rule = activation.rule
        return {
            "rule_id": rule.id,
            "rule_name": rule.name,
            "module": rule.module,
            "description": rule.description,
            "severity": rule.severity.value,
            "source": rule.source,
            "conclusion_key": rule.conclusion_key,
            "conclusion_label": rule.conclusion_label,
            "entities": dict(activation.entities),
            "conditions": [
                {
                    "Condition": evaluation.condition.describe(),
                    "Field": evaluation.condition.field,
                    "Operator": evaluation.condition.operator,
                    "Expected": str(evaluation.condition.value),
                    "Observed": "Unknown"
                    if not evaluation.known
                    else str(evaluation.observed),
                    "Status": evaluation.status,
                    "Note": evaluation.note,
                }
                for evaluation in activation.evaluations
            ],
        }

    def justification_markdown(self, activation: RuleActivation) -> str:
        data = self.justification(activation)
        header = [
            f"**Rule {data['rule_id']} - {data['rule_name']}**",
            f"*Module:* {data['module']}  |  *Severity:* {data['severity']}  |  "
            f"*Source:* {data['source']}",
            f"*Conclusion:* **{data['conclusion_label']}** (`{data['conclusion_key']}`)",
        ]
        table = ["| Condition | Observed | Status |", "|---|---|---|"]
        for row in data["conditions"]:
            table.append(f"| {row['Condition']} | {row['Observed']} | {row['Status']} |")
        closing = (
            "All conditions were satisfied, therefore the rule fired and the "
            "conclusion was inserted into working memory."
        )
        return "\n\n".join(header) + "\n\n" + "\n".join(table) + "\n\n" + closing

    # -- actions ------------------------------------------------------------
    @staticmethod
    def action_rows(investigation: Investigation) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for action in investigation.actions:
            rows.append(
                {
                    "ID": action.action_id,
                    "Phase": action.phase.value,
                    "Action": action.label,
                    "Target": f"{action.target_type}:{action.target}",
                    "Finding": action.finding_label,
                    "Priority": action.priority,
                    "Executable": "Yes" if action.executable else "No",
                    "Status": action.status,
                    "Blocked reason": action.blocked_reason,
                }
            )
        return rows

    @staticmethod
    def action_markdown(action: ResponseAction) -> str:
        paragraphs = [
            f"**{action.action_id} - {action.label}**",
            f"*Phase:* {action.phase.value}  |  *Priority:* {action.priority}  |  "
            f"*Target:* {action.target_type} `{action.target}`",
            f"*Selected because:* {action.reason}",
        ]
        if action.executable:
            paragraphs.append("*Target check:* target exists and is in a valid state.")
        else:
            paragraphs.append(f"*Blocked:* {action.blocked_reason}")
        if action.execution is not None:
            execution = action.execution
            paragraphs.append(
                f"*Execution:* **{execution.status}** - {execution.message}"
            )
            if execution.before or execution.after:
                paragraphs.append(
                    f"*State change:* `{execution.before}` → `{execution.after}`"
                )
        return "\n\n".join(paragraphs)

    # -- report -------------------------------------------------------------
    def markdown_report(self, investigation: Investigation) -> str:
        lines = [
            f"# CIARES Investigation Report - {investigation.id}",
            "",
            f"**Investigation:** {investigation.name}  ",
            f"**Started:** {investigation.started_at}  ",
            f"**Scenario:** {investigation.scenario_id or 'manual'}  ",
            f"**Inference:** {len(investigation.activations)} activations, "
            f"{investigation.terminated_reason}",
            "",
            "## Observations",
            "",
            "| Fact | Value |",
            "|---|---|",
        ]
        for key, value in investigation.observations.items():
            lines.append(f"| `{key}` | {value} |")

        lines.extend(["", "## Findings", "", "| Finding | Severity | Module | Rules |", "|---|---|---|---|"])
        for finding in investigation.findings:
            lines.append(
                f"| {finding.label} | {finding.severity.value} | {finding.module} | "
                f"{', '.join(finding.rule_ids)} |"
            )

        lines.extend(["", "## Inference trace", "", "| Step | Rule | Conclusion |", "|---|---|---|"])
        for activation in investigation.activations:
            lines.append(
                f"| {activation.sequence} | {activation.rule.id} | "
                f"{activation.conclusion_label} |"
            )

        lines.extend(["", "## Response actions", ""])
        for action in investigation.actions:
            lines.append(self.action_markdown(action))
            lines.append("")

        lines.extend(
            [
                "## Limitations",
                "",
                "All actions are executed against CIARES's internal simulated "
                "environment. No real account, host, process or network is modified.",
            ]
        )
        return "\n".join(lines)
