"""
Observation form schema.

This is presentation metadata only: the field keys are the fact names the rules
reference. No rule logic lives here.
"""

from __future__ import annotations

TRI_OPTIONS = ("Unknown", "True", "False")
TRI_VALUES: dict[str, bool | None] = {"Unknown": None, "True": True, "False": False}

OBSERVATION_SCHEMA: dict[str, list[tuple[str, str, str]]] = {
    "Authentication & Account Security": [
        ("failed_login_attempts", "Failed login attempts", "number"),
        ("successful_login_after_failures", "Successful login after failures", "tri"),
        ("unusual_login_location", "Unusual login location", "tri"),
        ("login_outside_working_hours", "Login outside working hours", "tri"),
        ("login_to_disabled_account", "Login attempted on a disabled account", "tri"),
        ("is_admin_account", "Account holds administrator privileges", "tri"),
        ("concurrent_sessions", "Concurrent sessions", "number"),
        ("mfa_failures", "MFA verification failures", "number"),
        ("unauthorized_password_change", "Unauthorized password change", "tri"),
        ("impossible_travel_detected", "Impossible travel detected", "tri"),
    ],
    "Malware & Process Security": [
        ("process_runs_from_unapproved_path", "Process runs from unapproved directory", "tri"),
        ("process_on_approved_list", "Process is on the approved list", "tri"),
        ("unauthorized_operation_attempted", "Process attempted an unauthorized operation", "tri"),
        ("protected_file_modified", "Protected file modified", "tri"),
        ("file_is_signed", "Executable is digitally signed", "tri"),
        ("spawns_shell", "Process spawned a command shell", "tri"),
        ("persistence_entry_added", "Startup/registry persistence entry added", "tri"),
        ("security_log_cleared", "Security log was cleared", "tri"),
        ("executable_hash_known", "Executable hash is known", "tri"),
        ("file_in_temp_directory", "File located in a temporary directory", "tri"),
    ],
    "Network Security": [
        ("destination_authorized", "Destination is authorized", "tri"),
        ("port_approved", "Port is approved", "tri"),
        ("remote_access_authorized", "Remote access is authorized", "tri"),
        ("suspicious_inbound_connection", "Suspicious inbound connection", "tri"),
        ("beaconing_interval_detected", "Regular beaconing interval detected", "tri"),
        ("unexpected_listening_service", "Unexpected listening service", "tri"),
        ("outbound_traffic_mb", "Outbound traffic (MB)", "number"),
        ("connection_attempts", "Connection attempts", "number"),
        ("denied_request_count", "Denied network requests", "number"),
    ],
    "Data Security & Protection": [
        ("transfer_volume_mb", "Transfer volume (MB)", "number"),
        ("download_count", "Files downloaded", "number"),
        ("transfer_destination_authorized", "Transfer destination is authorized", "tri"),
        ("restricted_file_accessed_unauthorized", "Restricted file accessed without authorization", "tri"),
        ("sensitive_file_shared_externally", "Sensitive file shared externally", "tri"),
        ("access_outside_permitted_hours", "Data accessed outside permitted hours", "tri"),
        ("data_modified_without_approval", "Data modified without approval", "tri"),
        ("protected_data_deleted", "Protected data deleted", "tri"),
    ],
    "Privilege & Security Policy": [
        ("unauthorized_privilege_escalation", "Unauthorized privilege escalation", "tri"),
        ("admin_privileges_granted", "Administrator privileges granted", "tri"),
        ("permission_change_approved", "Permission change was approved", "tri"),
        ("security_control_disabled", "Security control disabled", "tri"),
        ("admin_operation_unauthorized", "Unauthorized administrative operation", "tri"),
        ("security_config_changed_unapproved", "Security configuration changed without approval", "tri"),
        ("self_approval_detected", "Change was self-approved", "tri"),
        ("dormant_account_privileged", "Dormant account holds privileges", "tri"),
        ("restricted_resource_accessed_unauthorized", "Restricted resource accessed without permission", "tri"),
    ],
}
