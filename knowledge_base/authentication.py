"""
Module 1 - Authentication & Account Security (AUTH-01 ... AUTH-12).

Every rule is manually authored. Thresholds come from ``config.THRESHOLDS`` and
are project assumptions, not universal standards.

Tiers: AUTH-01..03, 05..10 are single-indicator rules; AUTH-04, 11, 12 corroborate
earlier conclusions so the reasoning chain is visible in the Inference Trace.
"""

from __future__ import annotations

from config import THRESHOLDS
from engine.models import Condition, Phase, Rule, Severity

MODULE = "Authentication & Account Security"

AUTH_RULES: tuple[Rule, ...] = (
    Rule(
        id="AUTH-01",
        name="Repeated Authentication Failure Detection",
        module=MODULE,
        description=(
            "Detects an account under sustained password guessing by counting "
            "failed authentication attempts in the observation window."
        ),
        conditions=(
            Condition(
                "failed_login_attempts",
                ">=",
                THRESHOLDS["failed_login_attempts"],
                f"failed login attempts >= {THRESHOLDS['failed_login_attempts']}",
            ),
        ),
        conclusion_key="repeated_authentication_failures",
        conclusion_label="Repeated authentication failures",
        severity=Severity.HIGH,
        source="MITRE ATT&CK",
        tags=("T1110", "brute-force"),
    ),
    Rule(
        id="AUTH-02",
        name="Successful Login After Failures",
        module=MODULE,
        description=(
            "A successful authentication immediately following a burst of "
            "failures is the classic signature of a guessed or sprayed password."
        ),
        conditions=(
            Condition(
                "successful_login_after_failures",
                "==",
                True,
                "a login succeeded after the failures",
            ),
        ),
        conclusion_key="suspicious_login_sequence",
        conclusion_label="Suspicious login sequence",
        severity=Severity.HIGH,
        source="MITRE ATT&CK",
        tags=("T1078", "valid-accounts"),
    ),
    Rule(
        id="AUTH-03",
        name="Unusual Login Location",
        module=MODULE,
        description=(
            "The successful authentication originated from a location the account "
            "has not used before, which breaks the expected behaviour baseline."
        ),
        conditions=(
            Condition(
                "unusual_login_location",
                "==",
                True,
                "login location is outside the usual pattern",
            ),
        ),
        conclusion_key="unusual_location_login",
        conclusion_label="Unusual-location login",
        severity=Severity.MEDIUM,
        source="MITRE ATT&CK",
        tags=("T1078", "geo-anomaly"),
    ),
    Rule(
        id="AUTH-04",
        name="Possible Account Compromise",
        module=MODULE,
        description=(
            "Corroborates three independent authentication indicators: sustained "
            "failures, a success that followed them, and an unusual location. "
            "None of the three alone justifies treating the account as compromised."
        ),
        conditions=(
            Condition(
                "repeated_authentication_failures",
                "==",
                True,
                "repeated authentication failures were derived",
            ),
            Condition(
                "suspicious_login_sequence",
                "==",
                True,
                "a login succeeded after repeated failures",
            ),
            Condition(
                "unusual_location_login",
                "==",
                True,
                "the login came from an unusual location",
            ),
        ),
        conclusion_key="possible_account_compromise",
        conclusion_label="Possible account compromise",
        severity=Severity.CRITICAL,
        source="NIST SP 800-61 Rev. 3",
        recommended_action="disable_account",
        action_phase=Phase.CONTAINMENT,
        entity_type="account",
        priority=1,
        tags=("T1078", "containment"),
    ),
    Rule(
        id="AUTH-05",
        name="Disabled Account Access Attempt",
        module=MODULE,
        description=(
            "An authentication attempt against an account that should be disabled "
            "indicates either a stale credential in use or an attempt to reactivate "
            "access outside the approved process."
        ),
        conditions=(
            Condition(
                "login_to_disabled_account",
                "==",
                True,
                "a login was attempted against a disabled account",
            ),
        ),
        conclusion_key="disabled_account_access_attempt",
        conclusion_label="Disabled-account access attempt",
        severity=Severity.HIGH,
        source="CISA Guidance",
        recommended_action="revoke_session",
        action_phase=Phase.CONTAINMENT,
        entity_type="session",
        priority=2,
        tags=("T1078", "stale-account"),
    ),
    Rule(
        id="AUTH-06",
        name="Off-Hours Administrator Login",
        module=MODULE,
        description=(
            "An administrator authenticating outside the configured working hours "
            "reduces the chance that the activity belongs to an approved change window."
        ),
        conditions=(
            Condition(
                "login_outside_working_hours",
                "==",
                True,
                "the login happened outside working hours",
            ),
            Condition(
                "is_admin_account",
                "==",
                True,
                "the account holds administrator privileges",
            ),
        ),
        conclusion_key="off_hours_admin_login",
        conclusion_label="Off-hours administrator login",
        severity=Severity.HIGH,
        source="MITRE ATT&CK",
        tags=("T1078.002", "off-hours"),
    ),
    Rule(
        id="AUTH-07",
        name="Excessive Concurrent Sessions",
        module=MODULE,
        description=(
            "More simultaneous sessions than the account normally uses suggests "
            "a credential being shared or used from an additional location."
        ),
        conditions=(
            Condition(
                "concurrent_sessions",
                ">=",
                THRESHOLDS["concurrent_sessions"],
                f"concurrent sessions >= {THRESHOLDS['concurrent_sessions']}",
            ),
        ),
        conclusion_key="excessive_concurrent_sessions",
        conclusion_label="Excessive concurrent sessions",
        severity=Severity.MEDIUM,
        source="MITRE ATT&CK",
        tags=("T1078", "session-anomaly"),
    ),
    Rule(
        id="AUTH-08",
        name="Unauthorized Password Change",
        module=MODULE,
        description=(
            "A password change performed outside the approved credential process is "
            "treated as credential tampering, because it can lock out the real owner."
        ),
        conditions=(
            Condition(
                "unauthorized_password_change",
                "==",
                True,
                "the password was changed without authorization",
            ),
        ),
        conclusion_key="credential_tampering",
        conclusion_label="Credential tampering",
        severity=Severity.HIGH,
        source="MITRE ATT&CK",
        tags=("T1098", "T1531"),
    ),
    Rule(
        id="AUTH-09",
        name="MFA Brute Force",
        module=MODULE,
        description=(
            "Repeated failed multi-factor verifications indicate automated attempts "
            "to satisfy the second factor rather than a user mistyping a code."
        ),
        conditions=(
            Condition(
                "mfa_failures",
                ">=",
                THRESHOLDS["mfa_failures"],
                f"MFA failures >= {THRESHOLDS['mfa_failures']}",
            ),
        ),
        conclusion_key="mfa_bruteforce_suspected",
        conclusion_label="MFA brute-force suspected",
        severity=Severity.HIGH,
        source="MITRE ATT&CK",
        tags=("T1110.003", "T1621"),
    ),
    Rule(
        id="AUTH-10",
        name="Impossible Travel",
        module=MODULE,
        description=(
            "Two authentications from locations that cannot be reached in the elapsed "
            "time imply the credential is in use from two places at once."
        ),
        conditions=(
            Condition(
                "impossible_travel_detected",
                "==",
                True,
                "impossible travel was detected between logins",
            ),
        ),
        conclusion_key="distributed_credential_use",
        conclusion_label="Distributed credential use",
        severity=Severity.CRITICAL,
        source="MITRE ATT&CK",
        tags=("T1078", "impossible-travel"),
    ),
    Rule(
        id="AUTH-11",
        name="Confirmed Credential Compromise",
        module=MODULE,
        description=(
            "Credential tampering combined with a corroborated compromise confirms "
            "that the attacker controls the credential, not merely that guessing occurred."
        ),
        conditions=(
            Condition(
                "credential_tampering",
                "==",
                True,
                "the credential was tampered with",
            ),
            Condition(
                "possible_account_compromise",
                "==",
                True,
                "the account was already assessed as possibly compromised",
            ),
        ),
        conclusion_key="confirmed_credential_compromise",
        conclusion_label="Confirmed credential compromise",
        severity=Severity.CRITICAL,
        source="NIST SP 800-61 Rev. 3",
        recommended_action="revoke_session",
        action_phase=Phase.CONTAINMENT,
        entity_type="session",
        priority=2,
        tags=("T1078", "T1098", "containment"),
    ),
    Rule(
        id="AUTH-12",
        name="Suspicious Active Session",
        module=MODULE,
        description=(
            "An off-hours administrative login that also holds an unusual number of "
            "simultaneous sessions is an active session that needs containment."
        ),
        conditions=(
            Condition(
                "off_hours_admin_login",
                "==",
                True,
                "an off-hours administrator login was derived",
            ),
            Condition(
                "excessive_concurrent_sessions",
                "==",
                True,
                "an abnormal number of concurrent sessions was derived",
            ),
        ),
        conclusion_key="suspicious_active_session",
        conclusion_label="Suspicious active session",
        severity=Severity.HIGH,
        source="CISA Guidance",
        recommended_action="revoke_session",
        action_phase=Phase.CONTAINMENT,
        entity_type="session",
        priority=2,
        tags=("T1078.002", "containment"),
    ),
)
