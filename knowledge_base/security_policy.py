"""
Module 5 - Privilege & Security Policy Management (POL-01 ... POL-12).

Reasons about privilege escalation, unauthorized grants, disabled security
controls, separation-of-duties violations and dormant privileged accounts, then
corroborates them into insider-threat and cross-module findings.
"""

from __future__ import annotations

from engine.models import Condition, Phase, Rule, Severity

MODULE = "Privilege & Security Policy"

POLICY_RULES: tuple[Rule, ...] = (
    Rule(
        id="POL-01",
        name="Privilege Escalation Detected",
        module=MODULE,
        description=(
            "The account obtained a higher privilege level through an unauthorized "
            "escalation, which is the defining privileged violation."
        ),
        conditions=(
            Condition(
                "unauthorized_privilege_escalation",
                "==",
                True,
                "privileges were escalated without authorization",
            ),
        ),
        conclusion_key="privilege_escalation_detected",
        conclusion_label="Privilege escalation detected",
        severity=Severity.CRITICAL,
        source="MITRE ATT&CK",
        tags=("T1068", "T1548"),
    ),
    Rule(
        id="POL-02",
        name="Unauthorized Privilege Assignment",
        module=MODULE,
        description=(
            "Administrator privileges were granted while the permission change was "
            "not approved, so the grant bypassed the authorization process."
        ),
        conditions=(
            Condition(
                "admin_privileges_granted",
                "==",
                True,
                "administrator privileges were granted",
            ),
            Condition(
                "permission_change_approved",
                "==",
                False,
                "the permission change was not approved",
            ),
        ),
        conclusion_key="unauthorized_privilege_assignment",
        conclusion_label="Unauthorized privilege assignment",
        severity=Severity.CRITICAL,
        source="NIST SP 800-61 Rev. 3",
        recommended_action="revoke_permissions",
        action_phase=Phase.RECOVERY,
        priority=5,
        tags=("T1098", "T1098.003", "recovery"),
    ),
    Rule(
        id="POL-03",
        name="Unauthorized Security-Control Change",
        module=MODULE,
        description=(
            "A security control was disabled without authorization, directly "
            "impairing the organisation's defences."
        ),
        conditions=(
            Condition(
                "security_control_disabled",
                "==",
                True,
                "a security control was disabled",
            ),
        ),
        conclusion_key="unauthorized_security_control_change",
        conclusion_label="Unauthorized security-control change",
        severity=Severity.CRITICAL,
        source="MITRE ATT&CK",
        tags=("T1562.001", "defence-impairment"),
    ),
    Rule(
        id="POL-04",
        name="Suspicious Privileged Activity",
        module=MODULE,
        description=(
            "An unapproved privilege grant was followed by an unauthorized "
            "administrative operation, so the new privilege was actually used."
        ),
        conditions=(
            Condition(
                "unauthorized_privilege_assignment",
                "==",
                True,
                "an unauthorized privilege assignment was derived",
            ),
            Condition(
                "admin_operation_unauthorized",
                "==",
                True,
                "an unauthorized administrative operation occurred",
            ),
        ),
        conclusion_key="suspicious_privileged_activity",
        conclusion_label="Suspicious privileged activity",
        severity=Severity.CRITICAL,
        source="NIST SP 800-61 Rev. 3",
        recommended_action="revoke_permissions",
        action_phase=Phase.RECOVERY,
        priority=5,
        tags=("T1098", "T1562.001", "recovery"),
    ),
    Rule(
        id="POL-05",
        name="Security Policy Violation",
        module=MODULE,
        description=(
            "A restricted resource was accessed without the permission the policy "
            "requires for that resource."
        ),
        conditions=(
            Condition(
                "restricted_resource_accessed_unauthorized",
                "==",
                True,
                "a restricted resource was accessed without permission",
            ),
        ),
        conclusion_key="security_policy_violation",
        conclusion_label="Security policy violation",
        severity=Severity.HIGH,
        source="MITRE ATT&CK",
        tags=("T1078", "T1530", "policy"),
    ),
    Rule(
        id="POL-06",
        name="Unauthorized Administrative Operation",
        module=MODULE,
        description=(
            "An administrative operation was performed outside the approved "
            "administrative process."
        ),
        conditions=(
            Condition(
                "admin_operation_unauthorized",
                "==",
                True,
                "an administrative operation was unauthorized",
            ),
        ),
        conclusion_key="unauthorized_admin_operation",
        conclusion_label="Unauthorized administrative operation",
        severity=Severity.HIGH,
        source="MITRE ATT&CK",
        tags=("T1098", "admin"),
    ),
    Rule(
        id="POL-07",
        name="Unauthorized Configuration Change",
        module=MODULE,
        description=(
            "A security configuration was changed without approval, which is "
            "configuration drift away from the approved baseline."
        ),
        conditions=(
            Condition(
                "security_config_changed_unapproved",
                "==",
                True,
                "security configuration changed without approval",
            ),
        ),
        conclusion_key="unauthorized_configuration_change",
        conclusion_label="Unauthorized configuration change",
        severity=Severity.MEDIUM,
        source="MITRE ATT&CK",
        tags=("T1562", "configuration"),
    ),
    Rule(
        id="POL-08",
        name="Separation-of-Duties Violation",
        module=MODULE,
        description=(
            "The same identity requested and approved a permission change, which "
            "defeats the separation-of-duties control."
        ),
        conditions=(
            Condition(
                "self_approval_detected",
                "==",
                True,
                "the change was approved by its own requester",
            ),
        ),
        conclusion_key="separation_of_duties_violation",
        conclusion_label="Separation-of-duties violation",
        severity=Severity.HIGH,
        source="NIST Cybersecurity Framework 2.0",
        tags=("T1098", "governance"),
    ),
    Rule(
        id="POL-09",
        name="Dormant Privileged Account Risk",
        module=MODULE,
        description=(
            "A privileged account that should be dormant still holds rights, which "
            "is a standing risk if the credential is reused."
        ),
        conditions=(
            Condition(
                "dormant_account_privileged",
                "==",
                True,
                "a dormant account still holds privileges",
            ),
        ),
        conclusion_key="dormant_privileged_account_risk",
        conclusion_label="Dormant privileged account risk",
        severity=Severity.MEDIUM,
        source="CISA Guidance",
        tags=("T1078.002", "dormant"),
    ),
    Rule(
        id="POL-10",
        name="Active Control Tampering",
        module=MODULE,
        description=(
            "A disabled security control combined with an unapproved configuration "
            "change is active tampering with the defence baseline."
        ),
        conditions=(
            Condition(
                "unauthorized_security_control_change",
                "==",
                True,
                "a security control was disabled without authorization",
            ),
            Condition(
                "unauthorized_configuration_change",
                "==",
                True,
                "security configuration changed without approval",
            ),
        ),
        conclusion_key="active_control_tampering",
        conclusion_label="Active control tampering",
        severity=Severity.CRITICAL,
        source="MITRE ATT&CK",
        tags=("T1562.001", "T1562", "tampering"),
    ),
    Rule(
        id="POL-11",
        name="Insider Threat Suspected",
        module=MODULE,
        description=(
            "A dormant privileged account that is actually used for suspicious "
            "privileged activity points to an insider rather than an external actor."
        ),
        conditions=(
            Condition(
                "dormant_privileged_account_risk",
                "==",
                True,
                "a dormant privileged account risk was derived",
            ),
            Condition(
                "suspicious_privileged_activity",
                "==",
                True,
                "suspicious privileged activity was derived",
            ),
        ),
        conclusion_key="insider_threat_suspected",
        conclusion_label="Insider threat suspected",
        severity=Severity.CRITICAL,
        source="CISA Guidance",
        recommended_action="escalate_to_analyst",
        action_phase=Phase.ESCALATION,
        priority=7,
        tags=("T1078.002", "T1098", "escalation"),
    ),
    Rule(
        id="POL-12",
        name="Coordinated Privilege Compromise",
        module=MODULE,
        description=(
            "Privilege escalation combined with a corroborated account compromise "
            "across the authentication module indicates a coordinated attack rather "
            "than two unrelated events."
        ),
        conditions=(
            Condition(
                "privilege_escalation_detected",
                "==",
                True,
                "privilege escalation was derived",
            ),
            Condition(
                "possible_account_compromise",
                "==",
                True,
                "the authentication module derived a possible account compromise",
            ),
        ),
        conclusion_key="coordinated_privilege_compromise",
        conclusion_label="Coordinated privilege compromise",
        severity=Severity.CRITICAL,
        source="NIST SP 800-61 Rev. 3",
        recommended_action="disable_account",
        action_phase=Phase.CONTAINMENT,
        priority=1,
        tags=("T1078", "T1098", "T1068", "containment"),
    ),
)
