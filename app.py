"""
CIARES - Cybersecurity Incident Analysis and Response Expert System.

This is the public portal and the entry point. It contains no cybersecurity
knowledge and no inference logic: it collects observations, hands them to
``engine.pipeline`` and presents the prose that ``engine.report`` produces.

Routes
------
/        public portal: Home, Investigate, Scenarios, Results (sidebar sections)
/admin   hidden administration portal (email + password)
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from config import APP_NAME, APP_TAGLINE
from engine.models import Investigation
from engine.pipeline import run_investigation
from engine.report import (
    approve,
    deferred_recommendations,
    evidence_rows,
    finding_paragraphs,
    friendly_time,
    headline,
    overview_paragraph,
    plan_steps,
    plan_text,
    reasoning_paragraphs,
    threat_score,
    threat_sentence,
    top_severity,
)
from knowledge_base.knowledge_acquisition import validate_catalogue
from knowledge_base.rule_registry import ALL_RULES, MODULES
from scenarios.sample_scenarios import SCENARIOS, get_scenario
from storage import init_db, save_investigation
from theme import (
    apply_theme,
    card,
    footer,
    hero,
    metric_row,
    page_title,
    severity_chip,
    threat_meter,
)

SECTIONS = ("Home", "Investigate", "Scenarios", "Results")

TRI_OPTIONS = ("Unknown", "True", "False")
TRI_VALUES: dict[str, bool | None] = {"Unknown": None, "True": True, "False": False}

# Presentation metadata only: the keys are the fact names the rules reference.
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

MODULE_BLURBS = {
    "Authentication & Account Security": "Credential guessing, suspicious sign-ins and account takeover.",
    "Malware & Process Security": "Unapproved executables, persistence and log tampering.",
    "Network Security": "Unauthorized destinations, beaconing and exposed services.",
    "Data Security & Protection": "Exfiltration, bulk downloads and unauthorized data access.",
    "Privilege & Security Policy": "Privilege escalation and violations of security policy.",
}


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
def init_state() -> None:
    init_db()
    st.session_state.setdefault("investigation", None)
    st.session_state.setdefault("section", "Home")
    st.session_state.setdefault("admin_ok", False)
    st.session_state.setdefault("admin_attempts", 0)


def current() -> Investigation | None:
    investigation = st.session_state.get("investigation")
    return investigation if isinstance(investigation, Investigation) else None


def go(section: str) -> None:
    # The sidebar radio owns st.session_state["section"], so a navigation
    # requested from inside a page is queued and applied before the radio is
    # rebuilt on the next run.
    st.session_state["_goto"] = section
    st.rerun()


def launch(
    observations: dict[str, Any],
    name: str,
    scenario_id: str | None = None,
) -> Investigation:
    """Run the pipeline once and keep the result in this browser session."""
    investigation = run_investigation(
        observations=observations,
        name=name,
        scenario_id=scenario_id,
    )
    # A new investigation must not inherit checkboxes from the previous one.
    for key in list(st.session_state.keys()):
        if key.startswith("approve_"):
            del st.session_state[key]
    st.session_state.investigation = investigation
    save_investigation(investigation)
    return investigation


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def render_sidebar() -> None:
    pending = st.session_state.pop("_goto", None)
    if pending:
        st.session_state["section"] = pending

    with st.sidebar:
        st.markdown(f"## {APP_NAME}")
        st.caption("Decision support for incident response")
        st.radio("Section", SECTIONS, key="section", label_visibility="collapsed")
        st.divider()
        investigation = current()
        if investigation is not None:
            st.caption(f"Loaded: {investigation.name}")
            st.caption(investigation.id)
        else:
            st.caption("No investigation loaded.")


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------
def home() -> None:
    hero()
    report = validate_catalogue(ALL_RULES)

    st.markdown("### What it does")
    columns = st.columns(3)
    cards = [
        (
            "Diagnose",
            "Compares what you observed against 60 explicit IF-THEN rules and names "
            "the issue, with a severity and a plain-language reason.",
        ),
        (
            "Explain",
            "Every conclusion lists the observations that supported it. Nothing is "
            "hidden behind a trained model.",
        ),
        (
            "Recommend, then wait",
            "Suggests containment, eradication, recovery and escalation steps. It "
            "does nothing until you approve them.",
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
            ("Distinct facts", report.distinct_condition_fields, "Facts referenced by conditions"),
            ("Modules", len(MODULES), "Specialised security areas"),
            ("Scenarios", len(SCENARIOS), "Ready-made investigations"),
            ("Response types", 15, "Recommendations in the catalogue"),
        ]
    )

    st.markdown("### How to use it")
    steps = st.columns(4)
    steps[0].markdown("**1 · Describe**\n\nEnter what was observed.")
    steps[1].markdown("**2 · Read the diagnosis**\n\nSee the issue, severity and reasoning.")
    steps[2].markdown("**3 · Review and approve**\n\nChoose the recommendations you accept.")
    steps[3].markdown("**4 · Get the plan**\n\nReceive a written response plan.")

    st.divider()
    left, right, _ = st.columns([1, 1, 3])
    if left.button("Start an investigation", type="primary", use_container_width=True):
        go("Investigate")
    if right.button("Try a scenario", use_container_width=True):
        go("Scenarios")

    st.info(
        "CIARES advises a human. It does not disable accounts, isolate hosts or "
        "change any real system.",
        icon="🛡️",
    )


# ---------------------------------------------------------------------------
# Investigate
# ---------------------------------------------------------------------------
def _field(container, key: str, label: str, kind: str) -> None:
    if kind == "number":
        container.number_input(label, min_value=0, step=1, value=0, key=f"obs_{key}")
    elif kind == "tri":
        container.selectbox(label, TRI_OPTIONS, index=0, key=f"obs_{key}")
    else:
        container.text_input(label, key=f"obs_{key}")


def _collect() -> dict[str, Any]:
    observations: dict[str, Any] = {}
    for fields in OBSERVATION_SCHEMA.values():
        for key, _label, kind in fields:
            raw = st.session_state.get(f"obs_{key}")
            if kind == "number":
                observations[key] = int(raw or 0)
            elif kind == "tri":
                value = TRI_VALUES.get(str(raw))
                if value is not None:
                    observations[key] = value
            elif raw:
                observations[key] = raw
    return observations


def investigate() -> None:
    page_title(
        "Investigate an incident",
        "Enter what was observed. Unknown means the fact was not provided and is "
        "different from False. A rule that needs an Unknown fact will not fire.",
    )

    with st.form("investigation_form", clear_on_submit=False):
        name = st.text_input(
            "Investigation name", placeholder="e.g. Suspicious administrator activity"
        )
        for group, fields in OBSERVATION_SCHEMA.items():
            with st.expander(group, expanded=group.startswith("Authentication")):
                columns = st.columns(2)
                for index, (key, label, kind) in enumerate(fields):
                    _field(columns[index % 2], key, label, kind)
        submitted = st.form_submit_button("Run investigation", type="primary")

    if submitted:
        launch(_collect(), name or "Manual investigation")
        go("Results")

    investigation = current()
    if investigation is not None and investigation.scenario_id is None:
        st.divider()
        st.caption(f"Last manual investigation: {investigation.name} · {investigation.id}")
        if st.button("Open its results"):
            go("Results")


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------
def _field_labels() -> dict[str, str]:
    return {
        key: label
        for fields in OBSERVATION_SCHEMA.values()
        for key, label, _kind in fields
    }


def scenarios() -> None:
    page_title(
        "Scenario laboratory",
        "Six ready-made investigations. Each supplies observations only - the "
        "diagnosis comes from the same engine used for manual investigations.",
    )

    scenario_ids = [scenario.id for scenario in SCENARIOS]
    selected_id = st.selectbox(
        "Scenario",
        scenario_ids,
        format_func=lambda sid: f"{sid} · {get_scenario(sid).name}",
    )
    scenario = get_scenario(selected_id)

    st.markdown(f"#### {scenario.name}")
    st.write(scenario.summary)

    labels = _field_labels()
    with st.expander("Observations in this scenario", expanded=True):
        for key, value in scenario.observations.items():
            st.markdown(f"- **{labels.get(key, key)}:** {value}")

    if st.button("Run this scenario", type="primary"):
        launch(scenario.observations, scenario.name, scenario_id=scenario.id)
        go("Results")

    investigation = current()
    if investigation is not None and investigation.scenario_id == scenario.id:
        st.divider()
        st.caption(f"Last run: {investigation.id}")
        if st.button("Open its results"):
            go("Results")


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
def _finding_block(title: str, severity, text: str) -> str:
    return (
        f'<div class="cihares-finding">'
        f"<h4>{title}{severity_chip(severity)}</h4>"
        f"<p>{text}</p></div>"
    )


def results() -> None:
    page_title(
        "Investigation results",
        "The diagnosis in plain language, the reasoning behind it, and the response "
        "that is waiting for your approval.",
    )

    investigation = current()
    if investigation is None:
        st.info(
            "No investigation loaded. Start one or load a scenario first.",
            icon="🧭",
        )
        if st.button("Start an investigation", type="primary"):
            go("Investigate")
        return

    st.caption(
        f"{investigation.name} · {investigation.id} · {investigation.started_at}"
        + (f" · scenario {investigation.scenario_id}" if investigation.scenario_id else "")
    )

    threat_meter(
        threat_score(investigation),
        threat_sentence(investigation),
        top_severity(investigation),
    )

    st.markdown(f"### {headline(investigation)}")
    st.write(overview_paragraph(investigation))

    if not investigation.findings:
        st.caption(
            "No response is recommended. Add the missing observations and run the "
            "investigation again if you believe the incident is present."
        )
        _evidence_expander(investigation)
        return

    st.markdown("#### Findings")
    for item in finding_paragraphs(investigation):
        severity = next(
            finding.severity
            for finding in investigation.findings
            if finding.label == item["title"]
        )
        st.markdown(
            _finding_block(item["title"], severity, item["text"]),
            unsafe_allow_html=True,
        )

    st.markdown("#### What led to this")
    for paragraph in reasoning_paragraphs(investigation):
        st.write(paragraph)

    st.divider()
    _recommendations(investigation)
    _evidence_expander(investigation)


def _recommendations(investigation: Investigation) -> None:
    ready = [action for action in investigation.actions if not action.deferred]
    deferred = deferred_recommendations(investigation)

    if not investigation.actions:
        st.markdown("#### Recommended response")
        st.caption(
            "The findings are diagnostic: no rule behind them recommends a response "
            "action. Monitor the incident and escalate if it develops."
        )
        return

    if investigation.approved_at:
        _approved_plan(investigation)
    else:
        st.markdown("#### Recommended response")
        st.caption("Tick the recommendations you accept, then approve them.")
        selected: list[str] = []
        for action in ready:
            checked = st.checkbox(
                f"{action.action_id} · {action.label}",
                value=True,
                key=f"approve_{action.action_id}",
            )
            st.caption(f"{action.phase.value} · {action.reason}")
            if checked:
                selected.append(action.action_id)

        if deferred:
            st.caption(
                f"{len(deferred)} recovery step(s) are deferred until containment is "
                "verified and are not part of this approval."
            )

        if st.button("Approve selected recommendations", type="primary", disabled=not selected):
            approve(investigation, selected)
            save_investigation(investigation)
            st.rerun()

    if deferred:
        with st.expander(f"Deferred until containment is verified ({len(deferred)})"):
            for action in deferred:
                st.markdown(f"**{action.label}** — {action.defer_reason}")


def _approved_plan(investigation: Investigation) -> None:
    st.markdown("#### Response plan")
    st.success(
        f"Approved {friendly_time(investigation.approved_at)}. "
        f"{len(investigation.approved_actions)} recommendation(s) accepted."
    )

    steps = plan_steps(investigation)
    st.markdown("\n".join(f"{index}. {step}" for index, step in enumerate(steps, start=1)))

    st.download_button(
        "Download the response plan (.txt)",
        data=plan_text(investigation).encode("utf-8"),
        file_name=f"{investigation.id}-response-plan.txt",
        mime="text/plain",
    )

    with st.expander("Revise the approval"):
        st.caption(
            "Clearing the approval returns to the recommendation list; no history is "
            "lost because the investigation stays in the audit store."
        )
        if st.button("Clear approval"):
            for action in investigation.actions:
                action.approved = False
            investigation.approved_at = ""
            save_investigation(investigation)
            st.rerun()


def _evidence_expander(investigation: Investigation) -> None:
    with st.expander("Technical evidence (administrative)"):
        st.caption(
            "Rule identifiers are shown here for audit only. The public explanation "
            "above deliberately uses plain language."
        )
        rows = evidence_rows(investigation)
        if rows:
            st.dataframe(rows, hide_index=True)
        else:
            st.caption("No rule activated for this investigation.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def public_portal() -> None:
    init_state()
    render_sidebar()
    renderers = {
        "Home": home,
        "Investigate": investigate,
        "Scenarios": scenarios,
        "Results": results,
    }
    renderers.get(st.session_state.section, home)()
    footer()


def main() -> None:
    st.set_page_config(
        page_title=f"{APP_NAME} · {APP_TAGLINE}",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_theme()

    import admin

    pages = [
        st.Page(public_portal, title=APP_NAME, url_path="", default=True),
        st.Page(admin.render, title="Administration", url_path="admin", visibility="hidden"),
    ]
    st.navigation(pages).run()


main()
