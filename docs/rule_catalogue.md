# CIARES Rule Catalogue

The knowledge base contains **60 manually authored IF-THEN rules** across five modules,
and **85 distinct logical conditions**. The in-app Knowledge Base page regenerates the
condition inventory from the actual `Rule` objects, so the counts in this document and in
the application cannot drift apart.

Every rule listed below is implemented and covered by `tests/test_coverage.py`, including
the assertion that all 60 rules fire in at least one shipped scenario.

Rule tiers:

* **Tier 1** derives one atomic indicator from observations.
* **Tier 2** corroborates two or more indicators into a finding.
* **Tier 3** combines findings (sometimes across modules) into an incident-level finding
  and an incident-level response.

Severity is a classification of the *finding*, not a claim that a breach occurred.

---

## Module 1 - Authentication & Account Security

| ID | Rule | IF (conditions) | THEN (fact) | Severity | Response | Status |
|---|---|---|---|---|---|---|
| AUTH-01 | Repeated Authentication Failure Detection | `failed_login_attempts >= 10` | `repeated_authentication_failures` | High | - | Implemented |
| AUTH-02 | Successful Login After Failures | `successful_login_after_failures is True` | `suspicious_login_sequence` | High | - | Implemented |
| AUTH-03 | Unusual Login Location | `unusual_login_location is True` | `unusual_location_login` | Medium | - | Implemented |
| AUTH-04 | Possible Account Compromise | AUTH-01 + AUTH-02 + AUTH-03 | `possible_account_compromise` | Critical | `disable_account` | Implemented |
| AUTH-05 | Disabled Account Access Attempt | `login_to_disabled_account is True` | `disabled_account_access_attempt` | High | `revoke_session` | Implemented |
| AUTH-06 | Off-Hours Administrator Login | `login_outside_working_hours` + `is_admin_account` | `off_hours_admin_login` | High | - | Implemented |
| AUTH-07 | Excessive Concurrent Sessions | `concurrent_sessions >= 3` | `excessive_concurrent_sessions` | Medium | - | Implemented |
| AUTH-08 | Unauthorized Password Change | `unauthorized_password_change is True` | `credential_tampering` | High | - | Implemented |
| AUTH-09 | MFA Brute Force | `mfa_failures >= 5` | `mfa_bruteforce_suspected` | High | - | Implemented |
| AUTH-10 | Impossible Travel | `impossible_travel_detected is True` | `distributed_credential_use` | Critical | - | Implemented |
| AUTH-11 | Confirmed Credential Compromise | AUTH-08 + AUTH-04 | `confirmed_credential_compromise` | Critical | `revoke_session` | Implemented |
| AUTH-12 | Suspicious Active Session | AUTH-06 + AUTH-07 | `suspicious_active_session` | High | `revoke_session` | Implemented |

## Module 2 - Malware & Process Security

| ID | Rule | IF (conditions) | THEN (fact) | Severity | Response | Status |
|---|---|---|---|---|---|---|
| MAL-01 | Unusual Executable Location | `process_runs_from_unapproved_path is True` | `unusual_executable_location` | Medium | - | Implemented |
| MAL-02 | Unapproved Process | `process_on_approved_list is False` | `unapproved_process` | Medium | - | Implemented |
| MAL-03 | Policy-Violating Process | `unauthorized_operation_attempted is True` | `policy_violating_process` | High | - | Implemented |
| MAL-04 | Suspicious Process Activity | MAL-02 + MAL-03 | `suspicious_process_activity` | High | `isolate_process` | Implemented |
| MAL-05 | Unauthorized File Modification | `protected_file_modified is True` | `unauthorized_file_modification` | High | - | Implemented |
| MAL-06 | Untrusted Executable | `file_is_signed is False` + MAL-01 | `untrusted_executable` | High | - | Implemented |
| MAL-07 | Suspicious Process Spawning | `spawns_shell is True` + MAL-02 | `suspicious_process_spawning` | High | - | Implemented |
| MAL-08 | Persistence Mechanism | `persistence_entry_added is True` | `persistence_mechanism_detected` | Critical | `quarantine_file` | Implemented |
| MAL-09 | Unknown Binary in Temp Directory | `executable_hash_known is False` + `file_in_temp_directory is True` | `unknown_binary_in_temp_directory` | High | - | Implemented |
| MAL-10 | Malware Activity Suspected | MAL-04 + MAL-05 | `malware_activity_suspected` | Critical | `terminate_process` | Implemented |
| MAL-11 | Log Tampering | `security_log_cleared is True` | `log_tampering_detected` | Critical | - | Implemented |
| MAL-12 | Active Intrusion With Concealment | MAL-08 + MAL-11 | `active_intrusion_with_concealment` | Critical | `isolate_endpoint` | Implemented |

## Module 3 - Network Security

| ID | Rule | IF (conditions) | THEN (fact) | Severity | Response | Status |
|---|---|---|---|---|---|---|
| NET-01 | Unauthorized Destination Access | `destination_authorized is False` | `unauthorized_destination_access` | High | `block_destination` | Implemented |
| NET-02 | Unusual Outgoing Traffic | `outbound_traffic_mb >= 500` | `unusual_outgoing_traffic` | Medium | - | Implemented |
| NET-03 | Unapproved Port Activity | `port_approved is False` | `unapproved_port_activity` | Medium | - | Implemented |
| NET-04 | Suspicious Network Connection | `connection_attempts >= 20` + NET-01 | `suspicious_network_connection` | High | `restrict_connection` | Implemented |
| NET-05 | Unauthorized Remote Access | `remote_access_authorized is False` | `unauthorized_remote_access` | Critical | - | Implemented |
| NET-06 | Exposed Network Service | `unexpected_listening_service is True` | `exposed_network_service` | Medium | - | Implemented |
| NET-07 | Suspicious Inbound Connection | `suspicious_inbound_connection is True` | `inbound_intrusion_indicator` | High | - | Implemented |
| NET-08 | Repeated Denied Requests | `denied_request_count >= 15` | `repeated_denied_requests` | Medium | - | Implemented |
| NET-09 | Command-and-Control Beaconing | `beaconing_interval_detected is True` | `command_and_control_beaconing` | Critical | - | Implemented |
| NET-10 | Network Exfiltration Pattern | NET-04 + NET-02 | `network_exfiltration_pattern` | Critical | - | Implemented |
| NET-11 | Remote Intrusion Suspected | NET-05 + NET-07 | `remote_intrusion_suspected` | Critical | `escalate_to_analyst` | Implemented |
| NET-12 | Active Network Compromise | NET-09 + NET-10 | `active_network_compromise` | Critical | `isolate_endpoint` | Implemented |

## Module 4 - Data Security & Protection

| ID | Rule | IF (conditions) | THEN (fact) | Severity | Response | Status |
|---|---|---|---|---|---|---|
| DATA-01 | Unusual Data Transfer | `transfer_volume_mb >= 1000` | `unusual_data_transfer` | Medium | - | Implemented |
| DATA-02 | Unauthorized Transfer Destination | `transfer_destination_authorized is False` | `unauthorized_transfer_destination` | High | - | Implemented |
| DATA-03 | Unauthorized Sensitive Data Access | `restricted_file_accessed_unauthorized is True` | `unauthorized_sensitive_data_access` | High | - | Implemented |
| DATA-04 | Potential Data Exfiltration | DATA-01 + DATA-02 | `potential_data_exfiltration` | Critical | `restrict_transfer` | Implemented |
| DATA-05 | Unauthorized Data Deletion | `protected_data_deleted is True` | `unauthorized_data_deletion` | High | - | Implemented |
| DATA-06 | Unapproved Data Modification | `data_modified_without_approval is True` | `unapproved_data_modification` | Medium | - | Implemented |
| DATA-07 | Sensitive Data Sharing | `sensitive_file_shared_externally is True` | `sensitive_data_sharing` | High | - | Implemented |
| DATA-08 | After-Hours Sensitive Access | `access_outside_permitted_hours` + DATA-03 | `after_hours_sensitive_access` | High | - | Implemented |
| DATA-09 | Bulk Data Download | `download_count >= 100` | `bulk_data_download` | Medium | - | Implemented |
| DATA-10 | Bulk Export to Unapproved Destination | DATA-09 + DATA-02 | `bulk_export_to_unapproved_destination` | Critical | - | Implemented |
| DATA-11 | Confirmed Data Exfiltration | DATA-04 + DATA-03 | `confirmed_data_exfiltration` | Critical | `apply_data_access_restriction` | Implemented |
| DATA-12 | Data Integrity Breach | DATA-06 + DATA-05 | `data_integrity_breach` | Critical | `escalate_to_analyst` | Implemented |

## Module 5 - Privilege & Security Policy

| ID | Rule | IF (conditions) | THEN (fact) | Severity | Response | Status |
|---|---|---|---|---|---|---|
| POL-01 | Privilege Escalation Detected | `unauthorized_privilege_escalation is True` | `privilege_escalation_detected` | Critical | - | Implemented |
| POL-02 | Unauthorized Privilege Assignment | `admin_privileges_granted` + `permission_change_approved is False` | `unauthorized_privilege_assignment` | Critical | `revoke_permissions` | Implemented |
| POL-03 | Unauthorized Security-Control Change | `security_control_disabled is True` | `unauthorized_security_control_change` | Critical | - | Implemented |
| POL-04 | Suspicious Privileged Activity | POL-02 + `admin_operation_unauthorized` | `suspicious_privileged_activity` | Critical | `revoke_permissions` | Implemented |
| POL-05 | Security Policy Violation | `restricted_resource_accessed_unauthorized is True` | `security_policy_violation` | High | - | Implemented |
| POL-06 | Unauthorized Admin Operation | `admin_operation_unauthorized is True` | `unauthorized_admin_operation` | High | - | Implemented |
| POL-07 | Unauthorized Configuration Change | `security_config_changed_unapproved is True` | `unauthorized_configuration_change` | Medium | - | Implemented |
| POL-08 | Separation-of-Duties Violation | `self_approval_detected is True` | `separation_of_duties_violation` | High | - | Implemented |
| POL-09 | Dormant Privileged Account Risk | `dormant_account_privileged is True` | `dormant_privileged_account_risk` | Medium | - | Implemented |
| POL-10 | Active Control Tampering | POL-03 + POL-07 | `active_control_tampering` | Critical | - | Implemented |
| POL-11 | Insider Threat Suspected | POL-09 + POL-04 | `insider_threat_suspected` | Critical | `escalate_to_analyst` | Implemented |
| POL-12 | Coordinated Privilege Compromise (cross-module) | POL-01 + AUTH-04 | `coordinated_privilege_compromise` | Critical | `disable_account` | Implemented |

---

## Condition inventory (generated from the rule objects)

The counts below are produced by `validate_catalogue(ALL_RULES)`; the Knowledge Base
page renders the same numbers at runtime, so documentation and application cannot drift.

| Module | Rules | Logical conditions |
|---|---|---|
| Authentication & Account Security | 12 | 17 |
| Malware & Process Security | 12 | 18 |
| Network Security | 12 | 16 |
| Data Security & Protection | 12 | 17 |
| Privilege & Security Policy | 12 | 17 |
| **Total** | **60** | **85** |

* Rules: **60** of 60
* Logical conditions: **85** (requirement: at least 50)
* Distinct fact fields referenced by conditions: **80**
* Validation: **no errors**

### Fact-field inventory

| Fact field | Conditions | Rules using it |
|---|---|---|
| `admin_operation_unauthorized` | 2 | 2 |
| `possible_account_compromise` | 2 | 2 |
| `unapproved_process` | 2 | 2 |
| `unauthorized_sensitive_data_access` | 2 | 2 |
| `unauthorized_transfer_destination` | 2 | 2 |
| `access_outside_permitted_hours` | 1 | 1 |
| `admin_privileges_granted` | 1 | 1 |
| `beaconing_interval_detected` | 1 | 1 |
| `bulk_data_download` | 1 | 1 |
| `command_and_control_beaconing` | 1 | 1 |
| `concurrent_sessions` | 1 | 1 |
| `connection_attempts` | 1 | 1 |
| `credential_tampering` | 1 | 1 |
| `data_modified_without_approval` | 1 | 1 |
| `denied_request_count` | 1 | 1 |
| `destination_authorized` | 1 | 1 |
| `dormant_account_privileged` | 1 | 1 |
| `dormant_privileged_account_risk` | 1 | 1 |
| `download_count` | 1 | 1 |
| `excessive_concurrent_sessions` | 1 | 1 |
| `executable_hash_known` | 1 | 1 |
| `failed_login_attempts` | 1 | 1 |
| `file_in_temp_directory` | 1 | 1 |
| `file_is_signed` | 1 | 1 |
| `impossible_travel_detected` | 1 | 1 |
| `inbound_intrusion_indicator` | 1 | 1 |
| `is_admin_account` | 1 | 1 |
| `log_tampering_detected` | 1 | 1 |
| `login_outside_working_hours` | 1 | 1 |
| `login_to_disabled_account` | 1 | 1 |
| `mfa_failures` | 1 | 1 |
| `network_exfiltration_pattern` | 1 | 1 |
| `off_hours_admin_login` | 1 | 1 |
| `outbound_traffic_mb` | 1 | 1 |
| `permission_change_approved` | 1 | 1 |
| `persistence_entry_added` | 1 | 1 |
| `persistence_mechanism_detected` | 1 | 1 |
| `policy_violating_process` | 1 | 1 |
| `port_approved` | 1 | 1 |
| `potential_data_exfiltration` | 1 | 1 |
| `privilege_escalation_detected` | 1 | 1 |
| `process_on_approved_list` | 1 | 1 |
| `process_runs_from_unapproved_path` | 1 | 1 |
| `protected_data_deleted` | 1 | 1 |
| `protected_file_modified` | 1 | 1 |
| `remote_access_authorized` | 1 | 1 |
| `repeated_authentication_failures` | 1 | 1 |
| `restricted_file_accessed_unauthorized` | 1 | 1 |
| `restricted_resource_accessed_unauthorized` | 1 | 1 |
| `security_config_changed_unapproved` | 1 | 1 |
| `security_control_disabled` | 1 | 1 |
| `security_log_cleared` | 1 | 1 |
| `self_approval_detected` | 1 | 1 |
| `sensitive_file_shared_externally` | 1 | 1 |
| `spawns_shell` | 1 | 1 |
| `successful_login_after_failures` | 1 | 1 |
| `suspicious_inbound_connection` | 1 | 1 |
| `suspicious_login_sequence` | 1 | 1 |
| `suspicious_network_connection` | 1 | 1 |
| `suspicious_privileged_activity` | 1 | 1 |
| `suspicious_process_activity` | 1 | 1 |
| `transfer_destination_authorized` | 1 | 1 |
| `transfer_volume_mb` | 1 | 1 |
| `unapproved_data_modification` | 1 | 1 |
| `unauthorized_configuration_change` | 1 | 1 |
| `unauthorized_data_deletion` | 1 | 1 |
| `unauthorized_destination_access` | 1 | 1 |
| `unauthorized_file_modification` | 1 | 1 |
| `unauthorized_operation_attempted` | 1 | 1 |
| `unauthorized_password_change` | 1 | 1 |
| `unauthorized_privilege_assignment` | 1 | 1 |
| `unauthorized_privilege_escalation` | 1 | 1 |
| `unauthorized_remote_access` | 1 | 1 |
| `unauthorized_security_control_change` | 1 | 1 |
| `unexpected_listening_service` | 1 | 1 |
| `unusual_data_transfer` | 1 | 1 |
| `unusual_executable_location` | 1 | 1 |
| `unusual_location_login` | 1 | 1 |
| `unusual_login_location` | 1 | 1 |
| `unusual_outgoing_traffic` | 1 | 1 |

## Authoring rules (kept for future extension)

1. A rule's conclusion key must never be the same as one of its own conditions.
2. A rule's conclusion key must not clash with an observation key in `app.py`, otherwise a
   confirmed observation and a derived fact compete for the same working-memory slot.
3. Tier 2 and Tier 3 rules must reference *derived* keys (the `THEN` column above), never
   raw observations, so the reasoning chain is visible in the Inference Trace.
4. Every module must end in at least one Critical incident-level finding with a response.
5. Every rule must cite one of the approved sources in `config.APPROVED_SOURCES`.
6. Every rule must fire in at least one scenario; `tests/test_coverage.py` enforces this.
