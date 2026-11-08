"""
Central configuration for CIARES.

Nothing in this file is a cybersecurity standard. Every number here is a
*project assumption* that makes the knowledge base deterministic and testable.
They are grouped in one place so they can be tuned during a demonstration and
cited honestly as "CIARES assumptions" in the report and the viva.
"""

from __future__ import annotations

from pathlib import Path

APP_NAME = "CIARES"
APP_TAGLINE = "Cybersecurity Incident Analysis and Response Expert System"
APP_DESCRIPTION = (
    "A rule-based Expert System that investigates security incidents, derives "
    "findings, recommends responses and executes them in a simulated environment."
)
APP_VERSION = "1.0.0"

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
HISTORY_PATH = DATA_DIR / "investigations.json"

# --------------------------------------------------------------------------
# CIARES threshold assumptions (not universal standards)
# --------------------------------------------------------------------------
THRESHOLDS: dict[str, float] = {
    "failed_login_attempts": 10,
    "concurrent_sessions": 3,
    "mfa_failures": 5,
    "outbound_traffic_mb": 500,
    "transfer_volume_mb": 1000,
    "download_count": 100,
    "connection_attempts": 20,
    "denied_requests": 15,
}

# Approved knowledge sources. Rules may only cite one of these.
APPROVED_SOURCES: tuple[str, ...] = (
    "NIST SP 800-61 Rev. 3",
    "NIST Cybersecurity Framework 2.0",
    "MITRE ATT&CK",
    "CISA Guidance",
    "CIARES Project Assumption",
)

# --------------------------------------------------------------------------
# Working-day assumption used by the after-hours rules
# --------------------------------------------------------------------------
WORKING_HOURS = (8, 18)  # 08:00 inclusive - 18:00 exclusive
