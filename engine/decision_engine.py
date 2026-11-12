"""
The Decision Engine.

The inference engine answers "what is happening?"; this module answers "what
should we do about it?" It turns findings into ordered response recommendations
and applies explicit decision rules:

1. An action is only recommended when a fired rule asks for it.
2. Identical actions are collapsed into one recommendation.
3. A Recovery action is deferred while a Containment action is still open,
   because restoring access before containment is verified would undo it.
4. Recommendations are ordered by response phase, then by declared priority.

This is pure policy: CIARES never touches a real account, host, process or
network. The analyst approves the recommendations and carries them out.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from .models import Finding, Phase, ResponseAction, Severity


@dataclass(frozen=True)
class ActionSpec:
    key: str
    label: str
    phase: Phase
    priority: int
    description: str = ""


# Response catalogue. Priorities are action priorities (1 = most urgent) and are
# deliberately separate from rule priorities used during inference.
ACTION_LIBRARY: dict[str, ActionSpec] = {
    "isolate_endpoint": ActionSpec(
        "isolate_endpoint", "Isolate affected endpoint", Phase.CONTAINMENT, 1,
        "Take the device off the network so the incident cannot spread to other systems.",
    ),
    "disable_account": ActionSpec(
        "disable_account", "Disable affected account", Phase.CONTAINMENT, 1,
        "Stop all further sign-in with the affected credential.",
    ),
    "restrict_transfer": ActionSpec(
        "restrict_transfer", "Restrict suspicious data transfer", Phase.CONTAINMENT, 1,
        "Stop the identified transfer before more data leaves the organisation.",
    ),
    "revoke_session": ActionSpec(
        "revoke_session", "Revoke suspicious session", Phase.CONTAINMENT, 2,
        "End the active session that the intruder is currently using.",
    ),
    "restrict_connection": ActionSpec(
        "restrict_connection", "Restrict suspicious connection", Phase.CONTAINMENT, 2,
        "Rate-limit or close the connection under investigation.",
    ),
    "block_destination": ActionSpec(
        "block_destination", "Block unauthorised destination", Phase.CONTAINMENT, 2,
        "Deny all traffic to the unapproved destination.",
    ),
    "isolate_process": ActionSpec(
        "isolate_process", "Isolate suspicious process", Phase.CONTAINMENT, 2,
        "Freeze the process while evidence is collected.",
    ),
    "lock_account": ActionSpec(
        "lock_account", "Lock affected account", Phase.CONTAINMENT, 3,
        "Lock the credential pending verification with the account owner.",
    ),
    "terminate_process": ActionSpec(
        "terminate_process", "Terminate suspicious process", Phase.ERADICATION, 3,
        "Stop the malicious process after containment.",
    ),
    "quarantine_file": ActionSpec(
        "quarantine_file", "Quarantine suspicious file", Phase.ERADICATION, 4,
        "Move the executable to quarantine so it cannot run again.",
    ),
    "apply_data_access_restriction": ActionSpec(
        "apply_data_access_restriction", "Apply data-access restriction", Phase.CONTAINMENT, 4,
        "Restrict the account to approved data sets only.",
    ),
    "revoke_permissions": ActionSpec(
        "revoke_permissions", "Revoke unauthorised permissions", Phase.RECOVERY, 5,
        "Withdraw the privileges that were not approved.",
    ),
    "restore_permissions": ActionSpec(
        "restore_permissions", "Restore approved permissions", Phase.RECOVERY, 5,
        "Return the account to the approved permission baseline.",
    ),
    "restore_account": ActionSpec(
        "restore_account", "Restore approved account status", Phase.RECOVERY, 6,
        "Re-enable the account once containment is complete and verified.",
    ),
    "escalate_to_analyst": ActionSpec(
        "escalate_to_analyst", "Escalate to security administrator", Phase.ESCALATION, 7,
        "Refer the investigation to a human owner for verification.",
    ),
}


class DecisionEngine:
    def __init__(self, library: dict[str, ActionSpec] | None = None) -> None:
        self.library = library or ACTION_LIBRARY

    # -- public API ---------------------------------------------------------
    def decide(
        self,
        findings: Sequence[Finding],
        investigation_id: str = "INV-LOCAL",
    ) -> list[ResponseAction]:
        ordered = sorted(
            (finding for finding in findings if finding.recommended_action),
            key=lambda finding: (-finding.severity.rank, finding.sequence),
        )

        proposed: list[ResponseAction] = []
        seen: dict[str, ResponseAction] = {}

        for finding in ordered:
            spec = self.library.get(finding.recommended_action or "")
            if spec is None:
                spec = ActionSpec(
                    key=finding.recommended_action or "unknown_action",
                    label=(finding.recommended_action or "unknown action").replace("_", " ").title(),
                    phase=finding.action_phase,
                    priority=99,
                )

            action = ResponseAction(
                action=spec.key,
                label=spec.label,
                phase=spec.phase,
                priority=spec.priority,
                finding_key=finding.key,
                finding_label=finding.label,
                finding_severity=finding.severity,
                reason=self._reason(finding, spec),
            )

            if spec.key in seen:
                first = seen[spec.key]
                first.reason += f" This also addresses {finding.label.lower()}."
                if finding.severity.rank > first.finding_severity.rank:
                    first.finding_severity = finding.severity
                continue
            seen[spec.key] = action
            proposed.append(action)

        self._defer_recovery(proposed)
        proposed.sort(key=lambda action: (action.phase.order, action.priority, action.action))
        for index, action in enumerate(proposed, start=1):
            action.action_id = f"ACT-{index:03d}"
        return proposed

    # -- internals ----------------------------------------------------------
    @staticmethod
    def _reason(finding: Finding, spec: ActionSpec) -> str:
        return (
            f"{finding.label} was diagnosed with {finding.severity.value.lower()} "
            f"severity. {spec.description}"
        )

    @staticmethod
    def _defer_recovery(actions: Iterable[ResponseAction]) -> None:
        """Keep recovery behind containment; never restore access mid-incident."""
        actions = list(actions)
        contained = any(action.phase is Phase.CONTAINMENT for action in actions)
        if not contained:
            return
        for action in actions:
            if action.phase is Phase.RECOVERY:
                action.deferred = True
                action.defer_reason = (
                    "Deferred: a containment action is still in progress. Recovery "
                    "is only started once containment has been verified."
                )


def findings_by_severity(findings: Sequence[Finding]) -> dict[Severity, list[Finding]]:
    """Helper for the UI: group findings without dropping any of them."""
    grouped: dict[Severity, list[Finding]] = {severity: [] for severity in Severity}
    for finding in findings:
        grouped[finding.severity].append(finding)
    return grouped
