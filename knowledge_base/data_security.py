"""
Module 4 - Data Security & Protection (DATA-01 ... DATA-12).

Reasons about data volume, destination authorization, sensitive-data access,
integrity changes and deletion, then combines them into exfiltration and
integrity findings.
"""

from __future__ import annotations

from config import THRESHOLDS
from engine.models import Condition, Phase, Rule, Severity

MODULE = "Data Security & Protection"

DATA_RULES: tuple[Rule, ...] = (
    Rule(
        id="DATA-01",
        name="Unusual Data Transfer",
        module=MODULE,
        description=(
            "A transfer volume above the configured threshold is abnormal for normal "
            "business operations and needs a destination check."
        ),
        conditions=(
            Condition(
                "transfer_volume_mb",
                ">=",
                THRESHOLDS["transfer_volume_mb"],
                f"transfer volume >= {THRESHOLDS['transfer_volume_mb']} MB",
            ),
        ),
        conclusion_key="unusual_data_transfer",
        conclusion_label="Unusual data transfer",
        severity=Severity.MEDIUM,
        source="MITRE ATT&CK",
        tags=("T1048", "volume-anomaly"),
    ),
    Rule(
        id="DATA-02",
        name="Unauthorized Transfer Destination",
        module=MODULE,
        description=(
            "The data was sent to a destination that is not approved for that "
            "classification of data."
        ),
        conditions=(
            Condition(
                "transfer_destination_authorized",
                "==",
                False,
                "the transfer destination is not authorized",
            ),
        ),
        conclusion_key="unauthorized_transfer_destination",
        conclusion_label="Unauthorized transfer destination",
        severity=Severity.HIGH,
        source="MITRE ATT&CK",
        tags=("T1567", "destination"),
    ),
    Rule(
        id="DATA-03",
        name="Unauthorized Sensitive-Data Access",
        module=MODULE,
        description=(
            "A restricted file was accessed without the authorization required for "
            "that classification."
        ),
        conditions=(
            Condition(
                "restricted_file_accessed_unauthorized",
                "==",
                True,
                "a restricted file was accessed without authorization",
            ),
        ),
        conclusion_key="unauthorized_sensitive_data_access",
        conclusion_label="Unauthorized sensitive-data access",
        severity=Severity.HIGH,
        source="MITRE ATT&CK",
        tags=("T1005", "T1530"),
    ),
    Rule(
        id="DATA-04",
        name="Potential Data Exfiltration",
        module=MODULE,
        description=(
            "An unusually large transfer to an unauthorized destination is the "
            "canonical exfiltration pattern and justifies containment of the transfer."
        ),
        conditions=(
            Condition(
                "unusual_data_transfer",
                "==",
                True,
                "the transfer volume is unusual",
            ),
            Condition(
                "unauthorized_transfer_destination",
                "==",
                True,
                "the destination is unauthorized",
            ),
        ),
        conclusion_key="potential_data_exfiltration",
        conclusion_label="Potential data exfiltration",
        severity=Severity.CRITICAL,
        source="NIST SP 800-61 Rev. 3",
        recommended_action="restrict_transfer",
        action_phase=Phase.CONTAINMENT,
        entity_type="transfer",
        priority=1,
        tags=("T1041", "T1567", "containment"),
    ),
    Rule(
        id="DATA-05",
        name="Unauthorized Data Deletion",
        module=MODULE,
        description=(
            "Deletion of protected data threatens availability and may be destructive "
            "or cover-up activity."
        ),
        conditions=(
            Condition(
                "protected_data_deleted",
                "==",
                True,
                "protected data was deleted",
            ),
        ),
        conclusion_key="unauthorized_data_deletion",
        conclusion_label="Unauthorized data deletion",
        severity=Severity.HIGH,
        source="MITRE ATT&CK",
        tags=("T1485", "T1486"),
    ),
    Rule(
        id="DATA-06",
        name="Unapproved Data Modification",
        module=MODULE,
        description=(
            "Data changed outside the approved change process threatens integrity and "
            "may indicate tampering with records."
        ),
        conditions=(
            Condition(
                "data_modified_without_approval",
                "==",
                True,
                "data was modified without approval",
            ),
        ),
        conclusion_key="unapproved_data_modification",
        conclusion_label="Unapproved data modification",
        severity=Severity.MEDIUM,
        source="MITRE ATT&CK",
        tags=("T1565", "integrity"),
    ),
    Rule(
        id="DATA-07",
        name="Sensitive Data Sharing",
        module=MODULE,
        description=(
            "A sensitive file was shared outside the organisation, moving data beyond "
            "the controls that protect it."
        ),
        conditions=(
            Condition(
                "sensitive_file_shared_externally",
                "==",
                True,
                "a sensitive file was shared externally",
            ),
        ),
        conclusion_key="sensitive_data_sharing",
        conclusion_label="Sensitive data sharing",
        severity=Severity.HIGH,
        source="MITRE ATT&CK",
        tags=("T1567.002", "sharing"),
    ),
    Rule(
        id="DATA-08",
        name="After-Hours Sensitive Access",
        module=MODULE,
        description=(
            "Sensitive-data access outside permitted hours is harder to justify and is "
            "a strong indicator of unauthorized activity."
        ),
        conditions=(
            Condition(
                "access_outside_permitted_hours",
                "==",
                True,
                "data was accessed outside permitted hours",
            ),
            Condition(
                "unauthorized_sensitive_data_access",
                "==",
                True,
                "restricted data was accessed without authorization",
            ),
        ),
        conclusion_key="after_hours_sensitive_access",
        conclusion_label="After-hours sensitive access",
        severity=Severity.HIGH,
        source="MITRE ATT&CK",
        tags=("T1530", "T1078", "off-hours"),
    ),
    Rule(
        id="DATA-09",
        name="Bulk Data Download",
        module=MODULE,
        description=(
            "A download count above the configured baseline suggests collection of data "
            "in preparation for exfiltration."
        ),
        conditions=(
            Condition(
                "download_count",
                ">=",
                THRESHOLDS["download_count"],
                f"downloads >= {THRESHOLDS['download_count']}",
            ),
        ),
        conclusion_key="bulk_data_download",
        conclusion_label="Bulk data download",
        severity=Severity.MEDIUM,
        source="MITRE ATT&CK",
        tags=("T1039", "collection"),
    ),
    Rule(
        id="DATA-10",
        name="Bulk Export to Unapproved Destination",
        module=MODULE,
        description=(
            "Bulk collection transferred to an unauthorized destination is a direct "
            "staging-to-exfiltration sequence."
        ),
        conditions=(
            Condition(
                "bulk_data_download",
                "==",
                True,
                "bulk downloading was derived",
            ),
            Condition(
                "unauthorized_transfer_destination",
                "==",
                True,
                "the destination is unauthorized",
            ),
        ),
        conclusion_key="bulk_export_to_unapproved_destination",
        conclusion_label="Bulk export to unapproved destination",
        severity=Severity.CRITICAL,
        source="MITRE ATT&CK",
        tags=("T1567", "T1039"),
    ),
    Rule(
        id="DATA-11",
        name="Confirmed Data Exfiltration",
        module=MODULE,
        description=(
            "An exfiltration pattern combined with unauthorized access to restricted "
            "files confirms that sensitive data left the environment."
        ),
        conditions=(
            Condition(
                "potential_data_exfiltration",
                "==",
                True,
                "an exfiltration pattern was derived",
            ),
            Condition(
                "unauthorized_sensitive_data_access",
                "==",
                True,
                "restricted data was accessed without authorization",
            ),
        ),
        conclusion_key="confirmed_data_exfiltration",
        conclusion_label="Confirmed data exfiltration",
        severity=Severity.CRITICAL,
        source="NIST SP 800-61 Rev. 3",
        recommended_action="apply_data_access_restriction",
        action_phase=Phase.CONTAINMENT,
        entity_type="account",
        priority=4,
        tags=("T1041", "T1567", "containment"),
    ),
    Rule(
        id="DATA-12",
        name="Data Integrity Breach",
        module=MODULE,
        description=(
            "Unauthorized modification together with deletion of protected data is a "
            "deliberate integrity breach rather than an operational mistake."
        ),
        conditions=(
            Condition(
                "unapproved_data_modification",
                "==",
                True,
                "data was modified without approval",
            ),
            Condition(
                "unauthorized_data_deletion",
                "==",
                True,
                "protected data was deleted",
            ),
        ),
        conclusion_key="data_integrity_breach",
        conclusion_label="Data integrity breach",
        severity=Severity.CRITICAL,
        source="CISA Guidance",
        recommended_action="escalate_to_analyst",
        action_phase=Phase.ESCALATION,
        entity_type="incident",
        priority=7,
        tags=("T1485", "T1565", "escalation"),
    ),
)
