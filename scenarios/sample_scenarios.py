"""
Predefined investigation scenarios.

A scenario supplies OBSERVATIONS only. It never supplies the diagnosis or a
hardcoded response - the same inference engine and decision engine process both
scenarios and manual input.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Scenario:
    id: str
    name: str
    summary: str
    observations: dict[str, Any]
    expected_findings: tuple[str, ...] = ()


SCN_001 = Scenario(
    id="SCN-001",
    name="Account Compromise Investigation",
    summary=(
        "Twenty-five failed logins followed by a successful login from an unusual "
        "location. The classic credential-guessing pattern."
    ),
    observations={
        "failed_login_attempts": 25,
        "successful_login_after_failures": True,
        "unusual_login_location": True,
        "login_to_disabled_account": False,
        "is_admin_account": True,
    },
    expected_findings=(
        "repeated_authentication_failures",
        "suspicious_login_sequence",
        "unusual_location_login",
        "possible_account_compromise",
    ),
)

SCN_002 = Scenario(
    id="SCN-002",
    name="Malware Activity Investigation",
    summary=(
        "An unsigned executable in a temporary directory spawns a shell, modifies a "
        "protected file, installs persistence and then clears the security log."
    ),
    observations={
        "process_runs_from_unapproved_path": True,
        "process_on_approved_list": False,
        "unauthorized_operation_attempted": True,
        "protected_file_modified": True,
        "file_is_signed": False,
        "spawns_shell": True,
        "persistence_entry_added": True,
        "security_log_cleared": True,
        "executable_hash_known": False,
        "file_in_temp_directory": True,
    },
    expected_findings=(
        "unapproved_process",
        "suspicious_process_activity",
        "persistence_mechanism_detected",
        "log_tampering_detected",
        "active_intrusion_with_concealment",
    ),
)

SCN_003 = Scenario(
    id="SCN-003",
    name="Network Intrusion Investigation",
    summary=(
        "An endpoint connects to an unapproved destination on an unapproved port with "
        "large outbound volume, repeated attempts and regular beaconing."
    ),
    observations={
        "destination_authorized": False,
        "outbound_traffic_mb": 850,
        "port_approved": False,
        "connection_attempts": 40,
        "remote_access_authorized": False,
        "suspicious_inbound_connection": True,
        "beaconing_interval_detected": True,
        "unexpected_listening_service": True,
        "denied_request_count": 25,
    },
    expected_findings=(
        "unauthorized_destination_access",
        "unusual_outgoing_traffic",
        "suspicious_network_connection",
        "command_and_control_beaconing",
        "active_network_compromise",
    ),
)

SCN_004 = Scenario(
    id="SCN-004",
    name="Data Exfiltration Investigation",
    summary=(
        "A restricted file is accessed without authorization and 4.2 GB is sent to an "
        "unapproved destination, after hours, together with external sharing."
    ),
    observations={
        "transfer_volume_mb": 4200,
        "transfer_destination_authorized": False,
        "restricted_file_accessed_unauthorized": True,
        "download_count": 350,
        "sensitive_file_shared_externally": True,
        "access_outside_permitted_hours": True,
    },
    expected_findings=(
        "unusual_data_transfer",
        "unauthorized_transfer_destination",
        "potential_data_exfiltration",
        "confirmed_data_exfiltration",
    ),
)

SCN_005 = Scenario(
    id="SCN-005",
    name="Privilege Escalation Investigation",
    summary=(
        "An administrator grant is made without approval, a security control is disabled, "
        "the change is self-approved and a dormant privileged account becomes active."
    ),
    observations={
        "unauthorized_privilege_escalation": True,
        "admin_privileges_granted": True,
        "permission_change_approved": False,
        "security_control_disabled": True,
        "admin_operation_unauthorized": True,
        "security_config_changed_unapproved": True,
        "self_approval_detected": True,
        "dormant_account_privileged": True,
        "restricted_resource_accessed_unauthorized": True,
        # Cross-module evidence: also seen during the authentication investigation.
        "failed_login_attempts": 14,
        "successful_login_after_failures": True,
        "unusual_login_location": True,
    },
    expected_findings=(
        "unauthorized_privilege_assignment",
        "possible_account_compromise",
        "coordinated_privilege_compromise",
    ),
)


SCN_006 = Scenario(
    id="SCN-006",
    name="Credential Abuse and Data Integrity Investigation",
    summary=(
        "An off-hours administrator account is used from an impossible location with "
        "MFA failures, a disabled-account login and concurrent sessions. The password "
        "is changed without authorization and protected data is modified and deleted."
    ),
    observations={
        # Authentication evidence.
        "failed_login_attempts": 18,
        "successful_login_after_failures": True,
        "unusual_login_location": True,
        "login_to_disabled_account": True,
        "login_outside_working_hours": True,
        "is_admin_account": True,
        "concurrent_sessions": 4,
        "mfa_failures": 7,
        "unauthorized_password_change": True,
        "impossible_travel_detected": True,
        # Data integrity evidence.
        "data_modified_without_approval": True,
        "protected_data_deleted": True,
    },
    expected_findings=(
        "disabled_account_access_attempt",
        "off_hours_admin_login",
        "excessive_concurrent_sessions",
        "credential_tampering",
        "mfa_bruteforce_suspected",
        "distributed_credential_use",
        "confirmed_credential_compromise",
        "suspicious_active_session",
        "unapproved_data_modification",
        "unauthorized_data_deletion",
        "data_integrity_breach",
    ),
)


SCENARIOS: tuple[Scenario, ...] = (SCN_001, SCN_002, SCN_003, SCN_004, SCN_005, SCN_006)

SCENARIOS_BY_ID: dict[str, Scenario] = {scenario.id: scenario for scenario in SCENARIOS}


def get_scenario(scenario_id: str) -> Scenario:
    try:
        return SCENARIOS_BY_ID[scenario_id]
    except KeyError as error:
        raise KeyError(f"No scenario registered with id {scenario_id!r}") from error
