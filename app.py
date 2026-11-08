"""
CIARES - Cybersecurity Incident Analysis and Response Expert System
Streamlit user interface (component 3 of the Expert System).

This file contains NO cybersecurity knowledge and NO inference logic. It only
collects observations, calls the engine packages, and renders their results.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from config import APP_DESCRIPTION, APP_NAME, APP_TAGLINE, APP_VERSION, DATA_DIR, HISTORY_PATH
from engine.explanation_engine import ExplanationEngine
from engine.models import Investigation, Severity
from engine.pipeline import run_investigation, severity_totals
from knowledge_base.knowledge_acquisition import validate_catalogue
from knowledge_base.rule_registry import ALL_RULES, MODULES, RULES_BY_MODULE, module_summary
from scenarios.sample_scenarios import SCENARIOS, get_scenario
from simulation import available_actions, execute

PAGES = (
    "Security Overview",
    "New Investigation",
    "Scenario Laboratory",
    "Knowledge Base",
    "Inference Trace",
    "Response Center",
    "Investigation History",
)

MAX_HISTORY = 25

TRI_OPTIONS = ("Unknown", "True", "False")
TRI_VALUES: dict[str, bool | None] = {"Unknown": None, "True": True, "False": False}

ENTITY_FIELDS = (
    ("account_id", "Account ID"),
    ("session_id", "Session ID"),
    ("process_id", "Process ID"),
    ("file_id", "File ID"),
    ("transfer_id", "Transfer ID"),
    ("destination_id", "Destination ID"),
    ("endpoint_id", "Endpoint ID"),
    ("connection_id", "Connection ID"),
)

# ---------------------------------------------------------------------------
# Observation input schema. The keys here are the fact names used by the rules.
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Persistence helpers (session state + best-effort JSON file)
# ---------------------------------------------------------------------------
def load_history() -> list[dict[str, Any]]:
    try:
        if HISTORY_PATH.exists():
            data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data[:MAX_HISTORY]
    except (OSError, json.JSONDecodeError):
        pass
    return []


def save_history(history: list[dict[str, Any]]) -> bool:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        HISTORY_PATH.write_text(
            json.dumps(history[:MAX_HISTORY], indent=2), encoding="utf-8"
        )
        return True
    except OSError:
        return False


def init_state() -> None:
    st.session_state.setdefault("history", load_history())
    st.session_state.setdefault("investigation", None)
    st.session_state.setdefault("flash", None)


def launch(
    observations: dict[str, Any],
    entities: dict[str, str],
    name: str,
    scenario_id: str | None = None,
) -> Investigation:
    investigation = run_investigation(
        observations=observations,
        entities=entities,
        name=name,
        scenario_id=scenario_id,
    )
    st.session_state.investigation = investigation
    st.session_state.history.insert(0, investigation.to_record())
    st.session_state.history = st.session_state.history[:MAX_HISTORY]
    save_history(st.session_state.history)
    return investigation


def update_history_record(investigation: Investigation) -> None:
    records = st.session_state.history
    for index, record in enumerate(records):
        if record.get("id") == investigation.id:
            records[index] = investigation.to_record()
            break
    st.session_state.history = records
    save_history(records)


# ---------------------------------------------------------------------------
# Small UI helpers
# ---------------------------------------------------------------------------
def severity_dataframe(findings) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Finding": finding.label,
                "Severity": finding.severity.value,
                "Module": finding.module,
                "Rules": ", ".join(finding.rule_ids),
            }
            for finding in findings
        ]
    )


def findings_dataframe(records: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Finding": finding["label"],
                "Severity": finding["severity"],
                "Module": finding["module"],
                "Rules": ", ".join(finding["rule_ids"]),
            }
            for record in records
            for finding in record.get("findings", [])
        ]
    )


def metric_row(items: list[tuple[str, Any, str]]) -> None:
    """Metrics wrap three per row so labels are never truncated."""
    for start in range(0, len(items), 3):
        chunk = items[start : start + 3]
        columns = st.columns(3)
        for column, (label, value, help_text) in zip(columns, chunk):
            column.metric(label, value, help=help_text)


def render_header() -> None:
    st.markdown(
        f"""
        <div class="cihares-hero">
            <div class="cihares-kicker">Rule-based Expert System · v{APP_VERSION}</div>
            <h1>{APP_NAME}</h1>
            <div class="cihares-sub">{APP_TAGLINE}</div>
            <div class="cihares-desc">{APP_DESCRIPTION}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def current_investigation() -> Investigation | None:
    investigation = st.session_state.get("investigation")
    return investigation if isinstance(investigation, Investigation) else None


def no_investigation_notice() -> None:
    st.info(
        "No investigation loaded. Run a manual investigation or load a scenario "
        "from the Scenario Laboratory.",
        icon="🧭",
    )


# ---------------------------------------------------------------------------
# Page 1 - Security Overview
# ---------------------------------------------------------------------------
def page_overview() -> None:
    st.subheader("Security Overview")
    history: list[dict[str, Any]] = st.session_state.history
    report = validate_catalogue(ALL_RULES)
    totals = severity_totals(history)
    findings_total = sum(len(record.get("findings", [])) for record in history)
    executed_total = sum(
        1
        for record in history
        for action in record.get("actions", [])
        if action.get("status") == "Executed"
    )

    metric_row(
        [
            ("Investigations", len(history), "Investigations recorded this session / history file"),
            ("Findings", findings_total, "Total findings derived by rule activations"),
            ("Critical", totals.get("Critical", 0), "Critical findings"),
            ("Rules", len(ALL_RULES), "Rules currently registered in the knowledge base"),
            ("Conditions", report.condition_count, "Distinct logical conditions across all rules"),
            ("Actions executed", executed_total, "Simulated response actions executed"),
        ]
    )

    left, right = st.columns([1.1, 1])

    with left:
        st.markdown("#### Severity distribution")
        if findings_total:
            severity_frame = pd.DataFrame(
                {
                    "Severity": ["Critical", "High", "Medium", "Low"],
                    "Findings": [
                        totals.get("Critical", 0),
                        totals.get("High", 0),
                        totals.get("Medium", 0),
                        totals.get("Low", 0),
                    ],
                }
            )
            st.bar_chart(severity_frame, x="Severity", y="Findings", height=260)
        else:
            st.caption(
                "No findings recorded yet. Run a scenario to populate the severity "
                "distribution."
            )

    with right:
        st.markdown("#### Knowledge base")
        st.dataframe(
            pd.DataFrame(module_summary()).rename(
                columns={"module": "Module", "rules": "Rules", "conditions": "Conditions"}
            ),
            hide_index=True,
        )
        status = "✅ catalogue valid" if report.ok else f"⚠️ {len(report.errors)} error(s)"
        st.caption(f"{report.summary()} · {status}")

    st.markdown("#### Recent investigations")
    if not history:
        st.caption("No investigations yet. Start with the Scenario Laboratory for a guided demonstration.")
        return

    recent = pd.DataFrame(
        [
            {
                "ID": record.get("id"),
                "Name": record.get("name"),
                "Started": record.get("started_at"),
                "Findings": len(record.get("findings", [])),
                "Critical": record.get("severity_counts", {}).get("Critical", 0),
                "Actions executed": sum(
                    1 for action in record.get("actions", []) if action.get("status") == "Executed"
                ),
            }
            for record in history[:8]
        ]
    )
    st.dataframe(recent, hide_index=True)


# ---------------------------------------------------------------------------
# Page 2 - New Investigation
# ---------------------------------------------------------------------------
def _render_field(container, key: str, label: str, kind: str) -> None:
    if kind == "number":
        container.number_input(label, min_value=0, step=1, value=0, key=f"obs_{key}")
    elif kind == "tri":
        container.selectbox(label, TRI_OPTIONS, index=0, key=f"obs_{key}")
    else:
        container.text_input(label, key=f"obs_{key}")


def page_new_investigation() -> None:
    st.subheader("New Investigation")
    st.caption(
        "Boolean observations use three states: True (confirmed), False (explicitly "
        "absent) and Unknown (not provided). Unknown facts never satisfy a rule."
    )

    with st.form("investigation_form", clear_on_submit=False):
        st.markdown("#### Investigation details")
        details = st.columns(2)
        name = details[0].text_input(
            "Investigation name", placeholder="e.g. Suspicious administrator activity"
        )
        entity_columns = st.columns(4)
        for index, (key, label) in enumerate(ENTITY_FIELDS):
            entity_columns[index % 4].text_input(label, key=f"entity_{key}")

        for group, fields in OBSERVATION_SCHEMA.items():
            with st.expander(group, expanded=group.startswith("Authentication")):
                columns = st.columns(2)
                for index, (key, label, kind) in enumerate(fields):
                    _render_field(columns[index % 2], key, label, kind)

        submitted = st.form_submit_button("Run Investigation", type="primary")

    if not submitted:
        return

    observations: dict[str, Any] = {}
    for fields in OBSERVATION_SCHEMA.values():
        for key, _label, kind in fields:
            raw = st.session_state.get(f"obs_{key}")
            if kind == "number":
                observations[key] = int(raw or 0)
            elif kind == "tri":
                value = TRI_VALUES.get(str(raw), None)
                if value is not None:
                    observations[key] = value
            else:
                if raw:
                    observations[key] = raw

    entities = {
        key: str(st.session_state.get(f"entity_{key}", "")).strip()
        for key, _label in ENTITY_FIELDS
    }
    entities = {key: value for key, value in entities.items() if value}

    if not observations:
        st.warning("No observations supplied. Every condition is Unknown, so no rule can fire.")
        return

    investigation = launch(
        observations, entities, name or "Manual Investigation"
    )
    st.success(
        f"{investigation.id}: {len(investigation.activations)} rule activation(s), "
        f"{len(investigation.findings)} finding(s), "
        f"{len(investigation.actions)} proposed action(s)."
    )
    if investigation.findings:
        st.dataframe(severity_dataframe(investigation.findings), hide_index=True)
    else:
        st.info(
            "No rule fired for these observations. That is a valid result: CIARES does "
            "not invent findings from missing evidence."
        )
    st.caption("Open Inference Trace for the reasoning and Response Center for actions.")


# ---------------------------------------------------------------------------
# Page 3 - Scenario Laboratory
# ---------------------------------------------------------------------------
def page_scenarios() -> None:
    st.subheader("Scenario Laboratory")
    st.caption(
        "Scenarios provide observations and entity IDs only. Diagnosis, responses and "
        "execution come from the same engine used for manual investigations."
    )

    scenario_ids = [scenario.id for scenario in SCENARIOS]
    selected_id = st.selectbox(
        "Scenario",
        scenario_ids,
        format_func=lambda sid: f"{sid} · {get_scenario(sid).name}",
    )
    scenario = get_scenario(selected_id)

    st.markdown(f"**{scenario.name}**")
    st.write(scenario.summary)

    left, right = st.columns([1.4, 1])
    with left:
        st.markdown("#### Observations")
        st.dataframe(
            pd.DataFrame(
                [
                    {"Fact": key, "Value": str(value)}
                    for key, value in scenario.observations.items()
                ]
            ),
            hide_index=True,
        )
    with right:
        st.markdown("#### Entities")
        if scenario.entities:
            st.dataframe(
                pd.DataFrame(
                    [{"Entity": key, "ID": value} for key, value in scenario.entities.items()]
                ),
                hide_index=True,
            )
        else:
            st.caption("No entity IDs supplied.")
        with st.expander("Expected chain (verification)"):
            st.caption(
                "The scenario supplies observations only. Every finding below must be "
                "derived by the inference engine, which is asserted by the test suite."
            )
            for key in scenario.expected_findings:
                st.markdown(f"- `{key}`")

    if st.button("Run scenario", type="primary"):
        investigation = launch(
            scenario.observations,
            scenario.entities,
            scenario.name,
            scenario_id=scenario.id,
        )
        st.success(
            f"{investigation.id}: {len(investigation.activations)} activation(s), "
            f"{len(investigation.findings)} finding(s)."
        )

    investigation = current_investigation()
    if investigation and investigation.scenario_id == scenario.id:
        st.markdown("#### Result of the last run")
        if investigation.findings:
            st.dataframe(severity_dataframe(investigation.findings), hide_index=True)
        else:
            st.warning("No finding was derived for this scenario, which would be a regression.")
        missing = [key for key in scenario.expected_findings if key not in {f.key for f in investigation.findings}]
        if missing:
            st.error("Expected but not derived (regression): " + ", ".join(f"`{key}`" for key in missing))


# ---------------------------------------------------------------------------
# Page 4 - Knowledge Base
# ---------------------------------------------------------------------------
def page_knowledge_base() -> None:
    st.subheader("Knowledge Base")
    report = validate_catalogue(ALL_RULES)

    metric_row(
        [
            ("Rules", len(ALL_RULES), "Manually authored IF-THEN rules"),
            ("Logical conditions", report.condition_count, "Assignment minimum is 50"),
            ("Distinct fact fields", report.distinct_condition_fields, "Unique facts referenced by conditions"),
            ("Modules", len(MODULES), "Specialised cybersecurity areas"),
        ]
    )

    if report.errors:
        st.error("Knowledge base validation failed:\n\n" + "\n".join(f"- {e}" for e in report.errors))
    else:
        st.success("Knowledge base structure is valid: unique IDs, conditions present, severities and sources approved.")

    tabs = st.tabs([f"{module} ({len(RULES_BY_MODULE[module])})" for module in MODULES])
    for tab, module in zip(tabs, MODULES):
        rules = RULES_BY_MODULE[module]
        with tab:
            if not rules:
                st.info("No rules are registered in this module.")
                continue
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Rule": rule.id,
                            "Name": rule.name,
                            "Conditions": rule.condition_count,
                            "Conclusion": rule.conclusion_label,
                            "Severity": rule.severity.value,
                            "Response": rule.recommended_action or "—",
                            "Source": rule.source,
                        }
                        for rule in rules
                    ]
                ),
                hide_index=True,
            )
            for rule in rules:
                with st.expander(f"{rule.id} · {rule.name}"):
                    st.write(rule.description)
                    st.dataframe(
                        pd.DataFrame(
                            [
                                {
                                    "Condition": condition.describe(),
                                    "Field": condition.field,
                                    "Operator": condition.operator,
                                    "Value": str(condition.value),
                                }
                                for condition in rule.conditions
                            ]
                        ),
                        hide_index=True,
                    )
                    st.markdown(
                        f"**IF** {rule.describe_conditions()}  \n"
                        f"**THEN** `{rule.conclusion_key}` = True "
                        f"({rule.conclusion_label})  \n"
                        f"**Severity** {rule.severity.value} · **Source** {rule.source}"
                    )

            if module == MODULES[0]:
                st.caption(
                    f"Module summary: {len(rules)} rules, "
                    f"{sum(rule.condition_count for rule in rules)} logical conditions."
                )

    st.markdown("#### Condition inventory")
    st.caption(
        "Machine-generated from the rule objects; this is the evidence for the "
        "50-condition requirement."
    )
    st.dataframe(
        pd.DataFrame(report.inventory).rename(
            columns={"field": "Fact field", "conditions": "Conditions", "rules": "Rules using it"}
        ),
        hide_index=True,
    )


# ---------------------------------------------------------------------------
# Page 5 - Inference Trace
# ---------------------------------------------------------------------------
def page_trace() -> None:
    st.subheader("Inference Trace")
    investigation = current_investigation()
    if investigation is None:
        no_investigation_notice()
        return

    st.caption(
        f"{investigation.id} · {investigation.name} · {len(investigation.activations)} "
        f"activations · {investigation.terminated_reason}"
    )

    tab_trace, tab_justify, tab_facts = st.tabs(
        ["Activation sequence", "Justification", "Working memory"]
    )

    engine = ExplanationEngine()

    with tab_trace:
        st.markdown("#### Rule activations")
        if investigation.activations:
            st.dataframe(
                pd.DataFrame(engine.activation_rows(investigation)),
                hide_index=True,
                column_config={
                    "#": st.column_config.NumberColumn(width="small"),
                },
            )
        else:
            st.info("No rule activated for this investigation.")
        st.markdown("#### Reasoning log")
        st.dataframe(
            pd.DataFrame(engine.trace_rows(investigation)),
            hide_index=True,
            column_config={
                "Step": st.column_config.NumberColumn(width="small"),
                "Event": st.column_config.TextColumn(width="small"),
                "Detail": st.column_config.TextColumn(width="large"),
            },
        )

    with tab_justify:
        if not investigation.activations:
            st.info("Nothing to justify yet.")
        else:
            ids = [activation.rule.id for activation in investigation.activations]
            chosen = st.selectbox("Rule activation", ids, key="justify_rule")
            activation = next(
                item for item in investigation.activations if item.rule.id == chosen
            )
            st.markdown(engine.justification_markdown(activation))
            st.dataframe(
                pd.DataFrame(engine.justification(activation)["conditions"]),
                hide_index=True,
            )
            missing = [
                key
                for key, value in investigation.observations.items()
                if value is None
            ]
            if missing:
                st.caption("Unknown observations: " + ", ".join(f"`{key}`" for key in missing))

    with tab_facts:
        memory = getattr(investigation, "memory", None)
        if memory is None:
            st.info("Working memory is only available for investigations run in this session.")
        else:
            st.markdown("#### Observations")
            st.dataframe(
                pd.DataFrame(
                    [
                        {"Fact": fact.key, "Value": fact.state, "Source": fact.source}
                        for fact in memory.observations()
                    ]
                ),
                hide_index=True,
            )
            st.markdown("#### Derived conclusions (with provenance)")
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Fact": fact.key,
                            "Value": fact.state,
                            "Derived by": fact.rule_id or "",
                            "Supporting facts": ", ".join(k for k, _ in fact.supporting),
                        }
                        for fact in memory.derived_facts()
                    ]
                ),
                hide_index=True,
            )

    with st.expander("Download this investigation report (Markdown)"):
        st.download_button(
            "Download report",
            data=engine.markdown_report(investigation).encode("utf-8"),
            file_name=f"{investigation.id}.md",
            mime="text/markdown",
        )


# ---------------------------------------------------------------------------
# Page 6 - Response Center
# ---------------------------------------------------------------------------
def page_response_center() -> None:
    st.subheader("Response Center")
    investigation = current_investigation()
    if investigation is None:
        no_investigation_notice()
        return

    engine = ExplanationEngine()
    st.caption(
        f"{investigation.id} · {investigation.name} · "
        f"{len(investigation.findings)} finding(s) · {len(investigation.actions)} proposed action(s)"
    )

    st.markdown("#### Diagnosis")
    if investigation.findings:
        st.dataframe(severity_dataframe(investigation.findings), hide_index=True)
    else:
        st.info("No findings were derived, therefore no response is justified.")

    st.markdown("#### Proposed responses")
    if not investigation.actions:
        st.caption(
            "No actionable finding. Diagnostic rules produce findings; only findings "
            "whose rule recommends a response create an action."
        )
        return

    st.dataframe(
        pd.DataFrame(engine.action_rows(investigation))[
            ["ID", "Phase", "Action", "Target", "Finding", "Executable", "Status"]
        ],
        hide_index=True,
    )

    proposed = [
        action
        for action in investigation.actions
        if action.executable and action.status == "Proposed"
    ]
    blocked = [action for action in investigation.actions if not action.executable]

    if blocked:
        with st.expander(f"Blocked actions ({len(blocked)})"):
            for action in blocked:
                st.markdown(f"- **{action.action_id} {action.label}** — {action.blocked_reason}")

    if not proposed:
        st.success("No further executable actions. Review the results below.")
    else:
        labels = {
            action.action_id: f"{action.action_id} · {action.label} → {action.target_type}:{action.target}"
            for action in proposed
        }
        approved = st.multiselect(
            "Approve simulated actions to execute",
            options=list(labels),
            default=list(labels),
            format_func=lambda action_id: labels[action_id],
        )
        st.caption(
            "Actions are executed against CIARES's internal simulated environment only. "
            "No real system is contacted or modified."
        )
        if st.button("Execute approved actions", type="primary", disabled=not approved):
            environment = investigation.environment
            results = []
            for action in proposed:
                if action.action_id in approved:
                    results.append(execute(environment, action))
            update_history_record(investigation)
            for result in results:
                if result.success:
                    st.success(f"{result.label}: {result.message}")
                else:
                    st.error(f"{result.label}: {result.message}")
            st.rerun()

    executed = [action for action in investigation.actions if action.execution is not None]
    if executed:
        st.markdown("#### Execution results")
        for action in executed:
            st.markdown(engine.action_markdown(action))
        st.markdown("#### Simulated environment after execution")
        environment = investigation.environment
        if environment is not None:
            st.dataframe(pd.DataFrame(environment.snapshot()), hide_index=True)

    with st.expander("Available simulated actions"):
        st.dataframe(
            pd.DataFrame(
                [{"Action": key, "Description": label} for key, label in available_actions().items()]
            ),
            hide_index=True,
        )


# ---------------------------------------------------------------------------
# Page 7 - Investigation History
# ---------------------------------------------------------------------------
def page_history() -> None:
    st.subheader("Investigation History")
    history: list[dict[str, Any]] = st.session_state.history

    if not history:
        st.info("No investigations recorded yet.")
        return

    summary = pd.DataFrame(
        [
            {
                "ID": record.get("id"),
                "Name": record.get("name"),
                "Started": record.get("started_at"),
                "Scenario": record.get("scenario_id") or "manual",
                "Findings": len(record.get("findings", [])),
                "Critical": record.get("severity_counts", {}).get("Critical", 0),
                "Executed": sum(
                    1 for action in record.get("actions", []) if action.get("status") == "Executed"
                ),
            }
            for record in history
        ]
    )
    st.dataframe(summary, hide_index=True)

    selected_id = st.selectbox(
        "Inspect investigation",
        [record.get("id") for record in history],
        format_func=lambda rid: next(
            (f"{record['id']} · {record['name']}" for record in history if record.get("id") == rid),
            str(rid),
        ),
    )
    record = next(record for record in history if record.get("id") == selected_id)

    left, right = st.columns(2)
    with left:
        st.markdown("#### Findings")
        st.dataframe(findings_dataframe([record]), hide_index=True)
    with right:
        st.markdown("#### Observations")
        st.dataframe(
            pd.DataFrame(
                [{"Fact": key, "Value": str(value)} for key, value in record.get("observations", {}).items()]
            ),
            hide_index=True,
        )

    st.markdown("#### Rule activations")
    st.dataframe(
        pd.DataFrame(record.get("activations", [])).rename(
            columns={
                "sequence": "#",
                "rule_id": "Rule",
                "rule_name": "Name",
                "conclusion": "Conclusion key",
                "conclusion_label": "Conclusion",
            }
        ),
        hide_index=True,
    )

    st.markdown("#### Response actions")
    actions = record.get("actions", [])
    if actions:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Action": action.get("label"),
                        "Target": f"{action.get('target_type')}:{action.get('target_id')}",
                        "Status": action.get("status"),
                        "Result": (action.get("execution") or {}).get("message", ""),
                    }
                    for action in actions
                ]
            ),
            hide_index=True,
        )
    else:
        st.caption("No response actions were proposed.")

    st.divider()
    left, right = st.columns(2)
    with left:
        st.download_button(
            "Download history (JSON)",
            data=json.dumps(history, indent=2).encode("utf-8"),
            file_name="cihares_history.json",
            mime="application/json",
        )
    with right:
        if st.button("Clear history"):
            st.session_state.history = []
            save_history([])
            st.session_state.investigation = None
            st.rerun()


# ---------------------------------------------------------------------------
# Sidebar + routing
# ---------------------------------------------------------------------------
def render_sidebar() -> str:
    report = validate_catalogue(ALL_RULES)
    st.sidebar.markdown(
        f"""
        <div class="cihares-side-brand">
            <div class="cihares-side-mark">🛡️</div>
            <div>
                <div class="cihares-side-title">{APP_NAME}</div>
                <div class="cihares-side-sub">Expert System</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    page = st.sidebar.radio("Navigation", PAGES)
    st.sidebar.divider()
    st.sidebar.caption("KNOWLEDGE BASE")
    st.sidebar.markdown(
        f"- **{len(ALL_RULES)}** rules\n"
        f"- **{report.condition_count}** logical conditions\n"
        f"- **{len(MODULES)}** modules"
    )
    if report.errors:
        st.sidebar.error(f"{len(report.errors)} validation error(s)")
    elif report.warnings:
        st.sidebar.warning(f"{len(report.warnings)} authoring warning(s)")
    st.sidebar.caption("All responses act on a simulated environment only.")
    return page


def main() -> None:
    st.set_page_config(
        page_title=f"{APP_NAME} · Expert System",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.6rem; max-width: 1300px;}
        .cihares-hero {
            background: linear-gradient(120deg, rgba(34,211,238,0.16), rgba(59,130,246,0.05));
            border: 1px solid rgba(34,211,238,0.25);
            border-radius: 18px;
            padding: 22px 26px;
            margin-bottom: 18px;
        }
        .cihares-kicker {font-size: 0.75rem; letter-spacing: 0.18em; text-transform: uppercase; color: #22d3ee;}
        .cihares-hero h1 {margin: 6px 0 2px 0; font-size: 2.4rem; letter-spacing: 0.04em;}
        .cihares-sub {font-size: 1.02rem; color: #e2e8f0;}
        .cihares-desc {font-size: 0.86rem; color: #94a3b8; margin-top: 6px; max-width: 900px;}
        .cihares-side-brand {display: flex; gap: 10px; align-items: center; margin-bottom: 12px;}
        .cihares-side-mark {font-size: 1.7rem;}
        .cihares-side-title {font-weight: 700; letter-spacing: 0.12em; font-size: 1.05rem;}
        .cihares-side-sub {font-size: 0.72rem; color: #22d3ee; letter-spacing: 0.16em; text-transform: uppercase;}
        [data-testid="stMetric"] {
            background: rgba(20,29,47,0.85);
            border: 1px solid rgba(148,163,184,0.16);
            border-radius: 14px;
            padding: 14px 16px;
        }
        [data-testid="stMetricLabel"] p {font-size: 0.78rem; letter-spacing: 0.06em; text-transform: uppercase;}
        h2, h3 {letter-spacing: 0.01em;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    init_state()
    page = render_sidebar()
    render_header()

    routes = {
        "Security Overview": page_overview,
        "New Investigation": page_new_investigation,
        "Scenario Laboratory": page_scenarios,
        "Knowledge Base": page_knowledge_base,
        "Inference Trace": page_trace,
        "Response Center": page_response_center,
        "Investigation History": page_history,
    }
    routes[page]()

    st.divider()
    st.caption(
        f"{APP_NAME} v{APP_VERSION} · {len(ALL_RULES)} rules · "
        f"forward chaining · simulated responses only · "
        f"built with Python and Streamlit"
    )


if __name__ == "__main__":
    main()
