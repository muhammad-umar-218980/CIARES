"""
Module 3 - Network Security (NET-01 ... NET-12).

Reasons about unauthorized destinations, traffic volume, unapproved ports, remote
access and command-and-control beaconing, then combines them into network
compromise findings.
"""

from __future__ import annotations

from config import THRESHOLDS
from engine.models import Condition, Phase, Rule, Severity

MODULE = "Network Security"

NETWORK_RULES: tuple[Rule, ...] = (
    Rule(
        id="NET-01",
        name="Unauthorized Destination Access",
        module=MODULE,
        description=(
            "The connection targets a destination that is not on the approved list, "
            "which is the first network-level policy violation."
        ),
        conditions=(
            Condition(
                "destination_authorized",
                "==",
                False,
                "the destination is not authorized",
            ),
        ),
        conclusion_key="unauthorized_destination_access",
        conclusion_label="Unauthorized destination access",
        severity=Severity.HIGH,
        source="MITRE ATT&CK",
        recommended_action="block_destination",
        action_phase=Phase.CONTAINMENT,
        entity_type="destination",
        priority=2,
        tags=("T1041", "T1071", "containment"),
    ),
    Rule(
        id="NET-02",
        name="Unusual Outgoing Traffic",
        module=MODULE,
        description=(
            "Outbound volume above the configured baseline suggests bulk data movement "
            "rather than normal application traffic."
        ),
        conditions=(
            Condition(
                "outbound_traffic_mb",
                ">=",
                THRESHOLDS["outbound_traffic_mb"],
                f"outbound traffic >= {THRESHOLDS['outbound_traffic_mb']} MB",
            ),
        ),
        conclusion_key="unusual_outgoing_traffic",
        conclusion_label="Unusual outgoing traffic",
        severity=Severity.MEDIUM,
        source="MITRE ATT&CK",
        tags=("T1048", "volume-anomaly"),
    ),
    Rule(
        id="NET-03",
        name="Unapproved Port Activity",
        module=MODULE,
        description=(
            "Traffic on a port that is not on the approved service list bypasses the "
            "expected network boundaries."
        ),
        conditions=(
            Condition("port_approved", "==", False, "the port is not approved"),
        ),
        conclusion_key="unapproved_port_activity",
        conclusion_label="Unapproved port activity",
        severity=Severity.MEDIUM,
        source="MITRE ATT&CK",
        tags=("T1571", "port-anomaly"),
    ),
    Rule(
        id="NET-04",
        name="Suspicious Network Connection",
        module=MODULE,
        description=(
            "Repeated connection attempts to an unauthorized destination indicate "
            "deliberate contact rather than a single mistyped address."
        ),
        conditions=(
            Condition(
                "connection_attempts",
                ">=",
                THRESHOLDS["connection_attempts"],
                f"connection attempts >= {THRESHOLDS['connection_attempts']}",
            ),
            Condition(
                "unauthorized_destination_access",
                "==",
                True,
                "the destination is unauthorized",
            ),
        ),
        conclusion_key="suspicious_network_connection",
        conclusion_label="Suspicious network connection",
        severity=Severity.HIGH,
        source="NIST SP 800-61 Rev. 3",
        recommended_action="restrict_connection",
        action_phase=Phase.CONTAINMENT,
        entity_type="connection",
        priority=2,
        tags=("T1071", "containment"),
    ),
    Rule(
        id="NET-05",
        name="Unauthorized Remote Access",
        module=MODULE,
        description=(
            "Remote access that the organisation did not authorize is a direct "
            "intrusion path into the environment."
        ),
        conditions=(
            Condition(
                "remote_access_authorized",
                "==",
                False,
                "remote access is not authorized",
            ),
        ),
        conclusion_key="unauthorized_remote_access",
        conclusion_label="Unauthorized remote access",
        severity=Severity.CRITICAL,
        source="MITRE ATT&CK",
        tags=("T1133", "T1021"),
    ),
    Rule(
        id="NET-06",
        name="Exposed Network Service",
        module=MODULE,
        description=(
            "A listening service that is not expected on this host widens the attack "
            "surface and may be left by an intruder."
        ),
        conditions=(
            Condition(
                "unexpected_listening_service",
                "==",
                True,
                "an unexpected service is listening",
            ),
        ),
        conclusion_key="exposed_network_service",
        conclusion_label="Exposed network service",
        severity=Severity.MEDIUM,
        source="MITRE ATT&CK",
        tags=("T1046", "exposure"),
    ),
    Rule(
        id="NET-07",
        name="Suspicious Inbound Connection",
        module=MODULE,
        description=(
            "Inbound connections that match exploitation or scanning patterns indicate "
            "an attempt to enter the environment from outside."
        ),
        conditions=(
            Condition(
                "suspicious_inbound_connection",
                "==",
                True,
                "an inbound connection looked suspicious",
            ),
        ),
        conclusion_key="inbound_intrusion_indicator",
        conclusion_label="Suspicious inbound connection",
        severity=Severity.HIGH,
        source="MITRE ATT&CK",
        tags=("T1190", "inbound"),
    ),
    Rule(
        id="NET-08",
        name="Repeated Denied Requests",
        module=MODULE,
        description=(
            "A high number of denied requests shows automated probing against closed "
            "or forbidden services."
        ),
        conditions=(
            Condition(
                "denied_request_count",
                ">=",
                THRESHOLDS["denied_requests"],
                f"denied requests >= {THRESHOLDS['denied_requests']}",
            ),
        ),
        conclusion_key="repeated_denied_requests",
        conclusion_label="Repeated denied requests",
        severity=Severity.MEDIUM,
        source="MITRE ATT&CK",
        tags=("T1595", "scanning"),
    ),
    Rule(
        id="NET-09",
        name="Command-and-Control Beaconing",
        module=MODULE,
        description=(
            "A regular beaconing interval is the signature of malware checking in with "
            "a command-and-control server."
        ),
        conditions=(
            Condition(
                "beaconing_interval_detected",
                "==",
                True,
                "a regular beaconing interval was detected",
            ),
        ),
        conclusion_key="command_and_control_beaconing",
        conclusion_label="Command-and-control beaconing",
        severity=Severity.CRITICAL,
        source="MITRE ATT&CK",
        tags=("T1071.001", "T1573", "c2"),
    ),
    Rule(
        id="NET-10",
        name="Network Exfiltration Pattern",
        module=MODULE,
        description=(
            "A suspicious connection to an unauthorized destination combined with "
            "abnormal outbound volume matches data leaving the network."
        ),
        conditions=(
            Condition(
                "suspicious_network_connection",
                "==",
                True,
                "a suspicious network connection was derived",
            ),
            Condition(
                "unusual_outgoing_traffic",
                "==",
                True,
                "outbound traffic is above the baseline",
            ),
        ),
        conclusion_key="network_exfiltration_pattern",
        conclusion_label="Network exfiltration pattern",
        severity=Severity.CRITICAL,
        source="MITRE ATT&CK",
        tags=("T1041", "T1048"),
    ),
    Rule(
        id="NET-11",
        name="Remote Intrusion Suspected",
        module=MODULE,
        description=(
            "Unauthorized remote access combined with suspicious inbound activity "
            "indicates an external party has entered the environment."
        ),
        conditions=(
            Condition(
                "unauthorized_remote_access",
                "==",
                True,
                "remote access is unauthorized",
            ),
            Condition(
                "inbound_intrusion_indicator",
                "==",
                True,
                "suspicious inbound activity was derived",
            ),
        ),
        conclusion_key="remote_intrusion_suspected",
        conclusion_label="Remote intrusion suspected",
        severity=Severity.CRITICAL,
        source="CISA Guidance",
        recommended_action="escalate_to_analyst",
        action_phase=Phase.ESCALATION,
        entity_type="incident",
        priority=7,
        tags=("T1133", "T1190", "escalation"),
    ),
    Rule(
        id="NET-12",
        name="Active Network Compromise",
        module=MODULE,
        description=(
            "Beaconing plus an exfiltration pattern is an active, ongoing network "
            "compromise that requires immediate containment of the endpoint."
        ),
        conditions=(
            Condition(
                "command_and_control_beaconing",
                "==",
                True,
                "command-and-control beaconing was derived",
            ),
            Condition(
                "network_exfiltration_pattern",
                "==",
                True,
                "an exfiltration pattern was derived",
            ),
        ),
        conclusion_key="active_network_compromise",
        conclusion_label="Active network compromise",
        severity=Severity.CRITICAL,
        source="NIST SP 800-61 Rev. 3",
        recommended_action="isolate_endpoint",
        action_phase=Phase.CONTAINMENT,
        entity_type="endpoint",
        priority=1,
        tags=("T1071", "T1041", "containment"),
    ),
)
