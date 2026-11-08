# CIARES Rule Sources

CIARES does not learn anything. Its knowledge is curated manually from published guidance
and translated into explicit IF-THEN rules. This document records the reference behind each
module and the assumptions that are *not* standards.

## Approved references

| Source | Edition used | What CIARES takes from it |
|---|---|---|
| **NIST SP 800-61 Rev. 3** — Incident Response Recommendations and Considerations for Cybersecurity Risk Management | April 2025 | Incident-response lifecycle; containment before eradication before recovery; the need to record evidence and justify response decisions |
| **NIST Cybersecurity Framework 2.0** | February 2024 | Vocabulary of Identify / Protect / Detect / Respond / Recover; governance of security controls; continuous monitoring |
| **MITRE ATT&CK** | Enterprise matrix (current) | Technique identifiers used to justify detection logic and to name observed attacker behaviour |
| **CISA Guidance** | #StopRansomware Guide, Incident & Vulnerability Response playbooks | Practical containment priorities, disabling compromised accounts, isolating endpoints, escalating to a human owner |
| **CIARES Project Assumption** | - | Numeric thresholds, working-hours definition and simulation state names |

Threshold values are collected in `config.THRESHOLDS` and are deliberately easy to change.
They must be presented as **project assumptions**, not as universal cybersecurity limits.

## MITRE ATT&CK mapping

### Authentication & Account Security

| Rule | Technique | Why |
|---|---|---|
| AUTH-01 | T1110 Brute Force | Sustained failed authentications are the observable signature of password guessing |
| AUTH-02 | T1078 Valid Accounts | A success after failures suggests a guessed password used as a valid account |
| AUTH-03 | T1078 Valid Accounts | Logging in from a new location is a valid-account anomaly |
| AUTH-04 | T1078, T1110 | Corroborates guessing with successful use from an unexpected place |
| AUTH-05 | T1078, T1098 Account Manipulation | Access to a disabled account implies stale or re-activated credentials |
| AUTH-06 | T1078.002 Domain Accounts | Off-hours administrator logins reduce the chance of a legitimate change window |
| AUTH-07 | T1078 | Multiple simultaneous sessions indicate credential sharing or theft |
| AUTH-08 | T1098, T1531 Account Access Removal | Password changes outside process are credential tampering |
| AUTH-09 | T1110.003 Password Spraying, T1621 MFA Request Generation | Repeated MFA failures indicate automated guessing |
| AUTH-10 | T1078 | Impossible travel implies the credential is in use from two places |
| AUTH-11 | T1078, T1098 | Combines tampering with a corroborated compromise |
| AUTH-12 | T1078.002 | Persistent, concurrent administrative sessions after hours |

### Malware & Process Security

| Rule | Technique | Why |
|---|---|---|
| MAL-01 | T1036 Masquerading | Execution from an unexpected directory is a masquerading signal |
| MAL-02 | T1204 User Execution | Not being on the approved list is an allow-list violation |
| MAL-03 | T1059 Command and Scripting Interpreter | Unauthorized operations indicate malicious capability |
| MAL-04 | T1059, T1204 | Corroboration of unapproved execution and unauthorized behaviour |
| MAL-05 | T1565 Data Manipulation, T1222 File Permissions Modification | Protected files should not change without an approved process |
| MAL-06 | T1027 Obfuscated Files, T1553 Subvert Trust Controls | Unsigned binaries in unusual paths break trust expectations |
| MAL-07 | T1059, T1105 Ingress Tool Transfer | A shell spawned by an unapproved process is a classic loader pattern |
| MAL-08 | T1547 Boot or Logon Autostart Execution, T1543 Create or Modify System Process | Persistence entries survive reboots |
| MAL-09 | T1027, T1105 | Unknown hashes in temporary directories evade allow-listing |
| MAL-10 | T1059, T1565 | Combined process and file evidence raises the finding to malware activity |
| MAL-11 | T1070.001 Clear Windows Event Logs | Clearing logs is deliberate anti-forensics |
| MAL-12 | T1070.001, T1547 | Persistence plus concealment is an active intrusion |

### Network Security

| Rule | Technique | Why |
|---|---|---|
| NET-01 | T1041 Exfiltration Over C2 Channel, T1071 Application Layer Protocol | Unauthorized destinations are the first network-level violation |
| NET-02 | T1048 Exfiltration Over Alternative Protocol | Volume anomalies precede or accompany exfiltration |
| NET-03 | T1571 Non-Standard Port | Unapproved ports bypass expected service boundaries |
| NET-04 | T1041, T1071 | Repetition plus an unauthorized destination indicates deliberate contact |
| NET-05 | T1133 External Remote Services, T1021 Remote Services | Remote access without authorization is a direct intrusion path |
| NET-06 | T1046 Network Service Discovery, T1203 Exploitation | Unexpected listening services widen the attack surface |
| NET-07 | T1190 Exploit Public-Facing Application | Suspicious inbound connections indicate probing or exploitation |
| NET-08 | T1046, T1595 Active Scanning | Repeated denials show automated probing |
| NET-09 | T1071.001 Web Protocols, T1573 Encrypted Channel | Regular intervals are the signature of C2 beaconing |
| NET-10 | T1041, T1048 | Exfiltration pattern across volume and destination anomalies |
| NET-11 | T1133, T1190 | External access plus inbound activity indicates intrusion |
| NET-12 | T1071, T1041 | Beaconing plus exfiltration is an active network compromise |

### Data Security & Protection

| Rule | Technique | Why |
|---|---|---|
| DATA-01 | T1048 | Volume thresholds detect abnormal data movement |
| DATA-02 | T1567 Exfiltration Over Web Service | Destination authorization is a data-governance control |
| DATA-03 | T1005 Data from Local System, T1530 Data from Cloud Storage | Restricted data must not be read without authorization |
| DATA-04 | T1041, T1567 | Volume plus destination anomaly is the canonical exfiltration pattern |
| DATA-05 | T1485 Data Destruction, T1486 Data Encrypted for Impact | Protected deletion threatens availability |
| DATA-06 | T1565 Data Manipulation | Unapproved modification threatens integrity |
| DATA-07 | T1567.002 Exfiltration to Cloud Storage | External sharing moves sensitive data out of control |
| DATA-08 | T1530, T1078 | After-hours access to restricted data breaks expected behaviour |
| DATA-09 | T1005, T1039 Data from Network Shared Drive | Bulk downloads precede exfiltration |
| DATA-10 | T1567, T1039 | Bulk movement to an unapproved destination |
| DATA-11 | T1041, T1567 | Corroborated exfiltration across data and network evidence |
| DATA-12 | T1485, T1565 | Integrity breach across modification and deletion |

### Privilege & Security Policy

| Rule | Technique | Why |
|---|---|---|
| POL-01 | T1068 Exploitation for Privilege Escalation, T1548 Abuse Elevation Control | Unauthorized escalation is the defining privileged violation |
| POL-02 | T1098 Account Manipulation, T1098.003 Additional Cloud Roles | Grants outside approval are unauthorized privilege assignment |
| POL-03 | T1562.001 Impair Defenses: Disable or Modify Tools | Disabling a control is direct defence impairment |
| POL-04 | T1098, T1562.001 | Assignment plus use of the new privilege is suspicious privileged activity |
| POL-05 | T1078, T1530 | Access to a restricted resource without permission is a policy violation |
| POL-06 | T1098 | Administrative operations outside approval |
| POL-07 | T1562 Impair Defenses | Configuration drift without approval weakens the baseline |
| POL-08 | T1098 | Self-approval breaks separation of duties |
| POL-09 | T1078.002 | Dormant privileged accounts are a standing risk |
| POL-10 | T1562.001, T1562 | Control disabled plus configuration change is active tampering |
| POL-11 | T1078.002, T1098 | Dormant privilege plus privileged activity suggests an insider |
| POL-12 | T1078, T1098, T1068 | Cross-module escalation from credential compromise to privilege abuse |

## NIST / CSF anchoring of the response model

| CIARES phase | NIST SP 800-61 Rev. 3 concept | CSF 2.0 function |
|---|---|---|
| Containment (`disable_account`, `revoke_session`, `isolate_endpoint`, `restrict_transfer`) | Limit the scope and impact of an incident | RS.MI (Incident Mitigation) |
| Eradication (`terminate_process`, `quarantine_file`) | Remove the adversary's presence and artefacts | RS.MI, PR.PS (Platform Security) |
| Recovery (`restore_permissions`, `restore_account`) | Return to a known-good, approved state | RC.RP (Recovery Plan Execution) |
| Escalation (`escalate_to_analyst`) | Hand off when evidence exceeds automated authority | RS.CO (Communication), GV.OV (Oversight) |

## Honesty notes for the report and viva

* CIARES encodes *detection heuristics*, not proof of compromise. A finding label such as
  "Possible account compromise" is deliberately cautious.
* Numeric thresholds are illustrative. Changing `config.THRESHOLDS` changes behaviour; the
  knowledge base contains no hidden constants.
* The MITRE mappings describe which attacker technique the logic reasons about. CIARES does
  not run ATT&CK evaluations and does not claim detection coverage scores.
* No rule encodes knowledge learned from data. The knowledge acquisition module records
  curated rules only.
