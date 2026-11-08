"""
The Decision Engine.

The inference engine answers "what is happening?"; this module answers "what
should we do about it?" It turns findings into concrete, targeted response
actions and applies explicit decision rules:

1. An action is only proposed when a rule that produced a finding recommends it.
2. The target must exist in the simulated environment.
3. The target must be in a state where the action makes sense.
4. Duplicate actions against the same target are collapsed into one.
5. A recovery action is suppressed when a containment action already exists for
   the same target (containment first - restoring access would undo it).
6. Actions are ordered by response phase and then by declared priority.

The engine never changes simulated state; that is the simulation layer's job.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, Sequence

from .models import Finding, Phase, ResponseAction, Severity

if TYPE_CHECKING:  # avoids importing the simulation at module import time
    from simulation.environment import SimulatedEnvironment


@dataclass(frozen=True)
class ActionSpec:
    key: str
    label: str
    phase: Phase
    priority: int
    target_type: str
    required_field: str = "status"
    required_values: frozenset[str] | None = None
    description: str = ""


# Response catalogue. Priorities are action priorities (1 = most urgent) and are
# deliberately separate from rule priorities used during inference.
ACTION_LIBRARY: dict[str, ActionSpec] = {
    "isolate_endpoint": ActionSpec(
        "isolate_endpoint", "Isolate affected endpoint", Phase.CONTAINMENT, 1, "endpoint",
        required_values=frozenset({"Online"}),
        description="Remove the endpoint from the simulated network to stop spread.",
    ),
    "disable_account": ActionSpec(
        "disable_account", "Disable affected account", Phase.CONTAINMENT, 1, "account",
        required_values=frozenset({"Active", "Locked"}),
        description="Prevent any further authentication with the affected credential.",
    ),
    "restrict_transfer": ActionSpec(
        "restrict_transfer", "Restrict suspicious data transfer", Phase.CONTAINMENT, 1, "transfer",
        required_values=frozenset({"Active"}),
        description="Stop the identified transfer before more data leaves.",
    ),
    "revoke_session": ActionSpec(
        "revoke_session", "Revoke suspicious session", Phase.CONTAINMENT, 2, "session",
        required_values=frozenset({"Active"}),
        description="Terminate the active session associated with the finding.",
    ),
    "restrict_connection": ActionSpec(
        "restrict_connection", "Restrict suspicious connection", Phase.CONTAINMENT, 2, "connection",
        required_values=frozenset({"Open"}),
        description="Rate-limit or close the connection under investigation.",
    ),
    "block_destination": ActionSpec(
        "block_destination", "Block unauthorized destination", Phase.CONTAINMENT, 2, "destination",
        required_values=frozenset({"Reachable"}),
        description="Deny all traffic to the unapproved destination.",
    ),
    "isolate_process": ActionSpec(
        "isolate_process", "Isolate suspicious process", Phase.CONTAINMENT, 2, "process",
        required_values=frozenset({"Running"}),
        description="Freeze the process while evidence is collected.",
    ),
    "lock_account": ActionSpec(
        "lock_account", "Lock affected account", Phase.CONTAINMENT, 3, "account",
        required_values=frozenset({"Active"}),
        description="Lock the credential pending verification with the account owner.",
    ),
    "terminate_process": ActionSpec(
        "terminate_process", "Terminate suspicious process", Phase.ERADICATION, 3, "process",
        required_values=frozenset({"Running", "Isolated"}),
        description="Stop the malicious process after containment.",
    ),
    "quarantine_file": ActionSpec(
        "quarantine_file", "Quarantine suspicious file", Phase.ERADICATION, 4, "file",
        required_values=frozenset({"Present"}),
        description="Move the executable to quarantine so it cannot run again.",
    ),
    "apply_data_access_restriction": ActionSpec(
        "apply_data_access_restriction", "Apply data-access restriction", Phase.CONTAINMENT, 4, "account",
        required_field="data_access",
        required_values=frozenset({"Unrestricted"}),
        description="Restrict the account to approved data sets only.",
    ),
    "revoke_permissions": ActionSpec(
        "revoke_permissions", "Revoke unauthorized permissions", Phase.RECOVERY, 5, "account",
        required_field="permissions",
        required_values=frozenset({"Approved", "Elevated"}),
        description="Withdraw the privileges that were not approved.",
    ),
    "restore_permissions": ActionSpec(
        "restore_permissions", "Restore approved permissions", Phase.RECOVERY, 5, "account",
        required_field="permissions",
        required_values=frozenset({"Revoked", "Elevated"}),
        description="Return the account to the approved permission baseline.",
    ),
    "restore_account": ActionSpec(
        "restore_account", "Restore approved account status", Phase.RECOVERY, 6, "account",
        required_values=frozenset({"Disabled", "Locked"}),
        description="Re-enable the account once containment is complete and verified.",
    ),
    "escalate_to_analyst": ActionSpec(
        "escalate_to_analyst", "Escalate to security administrator", Phase.ESCALATION, 7, "incident",
        description="Refer the investigation to a human owner.",
    ),
}


class DecisionEngine:
    def __init__(
        self,
        environment: "SimulatedEnvironment | None" = None,
        library: dict[str, ActionSpec] | None = None,
    ) -> None:
        self.environment = environment
        self.library = library or ACTION_LIBRARY

    # -- public API ---------------------------------------------------------
    def decide(
        self,
        findings: Sequence[Finding],
        entities: dict[str, str] | None = None,
        investigation_id: str = "INV-LOCAL",
    ) -> list[ResponseAction]:
        entities = dict(entities or {})
        ordered = sorted(
            (finding for finding in findings if finding.recommended_action),
            key=lambda finding: (-finding.severity.rank, finding.sequence),
        )

        proposed: list[ResponseAction] = []
        seen: dict[tuple[str, str | None], ResponseAction] = {}

        for finding in ordered:
            spec = self.library.get(finding.recommended_action or "")
            if spec is None:
                spec = ActionSpec(
                    key=finding.recommended_action or "unknown_action",
                    label=(finding.recommended_action or "unknown action").replace("_", " ").title(),
                    phase=finding.action_phase,
                    priority=99,
                    target_type=finding.entity_type or "account",
                )

            target_id = self._resolve_target(spec, entities, investigation_id)
            action = ResponseAction(
                action=spec.key,
                label=spec.label,
                phase=spec.phase,
                priority=spec.priority,
                target_type=spec.target_type,
                target_id=target_id,
                finding_key=finding.key,
                finding_label=finding.label,
                finding_severity=finding.severity,
                reason=self._reason(finding, spec),
            )
            action.action_id = f"ACT-{len(proposed) + 1:03d}"
            self._validate_target(action, spec)

            identity = (action.action, action.target_id)
            if identity in seen:
                first = seen[identity]
                first.reason += f"; also recommended by {finding.label}"
                if finding.severity.rank > first.finding_severity.rank:
                    first.finding_severity = finding.severity
                continue
            seen[identity] = action
            proposed.append(action)

        self._suppress_recovery_after_containment(proposed)
        proposed.sort(key=lambda action: (action.phase.order, action.priority, action.action))
        for index, action in enumerate(proposed, start=1):
            action.action_id = f"ACT-{index:03d}"
        return proposed

    # -- internals ----------------------------------------------------------
    @staticmethod
    def _resolve_target(
        spec: ActionSpec, entities: dict[str, str], investigation_id: str
    ) -> str | None:
        if spec.target_type == "incident":
            return investigation_id
        return entities.get(f"{spec.target_type}_id")

    @staticmethod
    def _reason(finding: Finding, spec: ActionSpec) -> str:
        basis = f"{finding.label} ({finding.severity.value} finding)"
        return f"{spec.label} is recommended because of {basis}"

    def _validate_target(self, action: ResponseAction, spec: ActionSpec) -> None:
        if spec.target_type == "incident":
            return
        if not action.target_id:
            action.executable = False
            action.blocked_reason = (
                f"No {spec.target_type} identifier was supplied, so the action "
                f"cannot target a simulated entity"
            )
            return
        if self.environment is None:
            return
        if not self.environment.exists(spec.target_type, action.target_id):
            action.executable = False
            action.blocked_reason = (
                f"{spec.target_type.title()} {action.target_id} does not exist in the "
                f"simulated environment; execution would be rejected"
            )
            return
        current = self.environment.field_of(spec.target_type, action.target_id, spec.required_field)
        if spec.required_values is not None and current not in spec.required_values:
            action.executable = False
            action.blocked_reason = (
                f"{spec.target_type.title()} {action.target_id} is currently "
                f"{current or 'in an unknown state'}; the action requires "
                f"{' or '.join(sorted(spec.required_values))}"
            )

    @staticmethod
    def _suppress_recovery_after_containment(actions: Iterable[ResponseAction]) -> None:
        contained = {
            (action.target_type, action.target_id)
            for action in actions
            if action.phase is Phase.CONTAINMENT and action.executable
        }
        for action in actions:
            if action.phase is not Phase.RECOVERY:
                continue
            if (action.target_type, action.target_id) in contained and action.executable:
                action.executable = False
                action.status = "Skipped"
                action.blocked_reason = (
                    "A containment action is already applied to this target; "
                    "recovery is deferred until containment is verified"
                )


def findings_by_severity(findings: Sequence[Finding]) -> dict[Severity, list[Finding]]:
    """Helper for the UI: group findings without dropping any of them."""
    grouped: dict[Severity, list[Finding]] = {severity: [] for severity in Severity}
    for finding in findings:
        grouped[finding.severity].append(finding)
    return grouped
