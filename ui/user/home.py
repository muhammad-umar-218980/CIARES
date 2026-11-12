"""Public home page: what CIARES is and what it does (never how it reasons)."""

from __future__ import annotations

import streamlit as st

from knowledge_base.knowledge_acquisition import validate_catalogue
from knowledge_base.rule_registry import ALL_RULES, MODULES
from scenarios.sample_scenarios import SCENARIOS
from simulation import available_actions
from ui.navigation import go
from ui.shared.layout import card, hero, metric_row

MODULE_BLURBS = {
    "Authentication & Account Security": "Credential guessing, suspicious sign-ins and account takeover.",
    "Malware & Process Security": "Unapproved executables, persistence and log tampering.",
    "Network Security": "Unauthorized destinations, beaconing, scans and exposed services.",
    "Data Security & Protection": "Exfiltration, bulk downloads and unauthorized data access.",
    "Privilege & Security Policy": "Privilege escalation and violations of security policy.",
}


def render() -> None:
    hero()
    report = validate_catalogue(ALL_RULES)

    st.markdown("### What it does")
    columns = st.columns(3)
    cards = [
        (
            "Diagnose",
            "Compares the observations you supply against a knowledge base of "
            "explicit IF-THEN rules and names what is happening, with severity.",
        ),
        (
            "Explain",
            "Every finding can be opened to show the rule that produced it and the "
            "conditions that were satisfied. No black box.",
        ),
        (
            "Recommend and act",
            "Proposes response actions, states why each one qualifies, and waits for "
            "your approval before changing the simulated environment.",
        ),
    ]
    for column, (title, body) in zip(columns, cards):
        column.markdown(card(title, body), unsafe_allow_html=True)

    st.markdown("### Five knowledge modules")
    module_columns = st.columns(3)
    for index, module in enumerate(MODULES):
        module_columns[index % 3].markdown(
            card(module, MODULE_BLURBS.get(module, "Specialised security rules.")),
            unsafe_allow_html=True,
        )

    st.markdown("### What is inside")
    metric_row(
        [
            ("Rules", len(ALL_RULES), "Manually authored IF-THEN rules"),
            ("Logical conditions", report.condition_count, "Conditions inside those rules"),
            ("Distinct facts", report.distinct_condition_fields, "Observation fields the rules use"),
            ("Modules", len(MODULES), "Specialised security areas"),
            ("Scenarios", len(SCENARIOS), "Ready-made investigations"),
            ("Response types", len(available_actions()), "Simulated response actions"),
        ]
    )
    st.caption(
        "The knowledge base is valid and loaded: "
        f"{report.rule_count} rules, {report.condition_count} conditions."
    )

    st.markdown("### How to use it")
    steps = st.columns(3)
    steps[0].markdown(
        "**1 · Describe the incident**\n\n"
        "Enter what was observed. Unknown means *not provided* and is different "
        "from False."
    )
    steps[1].markdown(
        "**2 · Read the diagnosis**\n\n"
        "Findings are ordered by severity. Open any finding to see the rule and "
        "the conditions behind it."
    )
    steps[2].markdown(
        "**3 · Approve a response**\n\n"
        "Choose which proposed actions to execute. Nothing runs without your "
        "approval."
    )

    st.divider()
    left, right, _ = st.columns([1, 1, 3])
    if left.button("Start an investigation", type="primary", use_container_width=True):
        go("investigate")
    if right.button("Try a scenario", use_container_width=True):
        go("scenarios")

    st.info(
        "This is a rule-based Expert System: every conclusion comes from an explicit "
        "rule, not from a trained model. Responses act on an internal simulated "
        "environment only.",
        icon="🛡️",
    )
