"""
The hidden administration portal (``/admin``).

Sign-in gate followed by six tabs: Dashboard, Knowledge base, Inference engine,
Decision engine, Audit and System map. This is the only place where rule
identifiers and technical tables are shown by default; the public portal explains
the same reasoning in prose.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from config import PROJECT_ROOT
from engine.decision_engine import ACTION_LIBRARY
from engine.explanation_engine import ExplanationEngine
from engine.models import Investigation
from knowledge_base.knowledge_acquisition import validate_catalogue
from knowledge_base.rule_registry import ALL_RULES, MODULES, RULES_BY_MODULE, module_summary
from passwords import verify_credentials
from scenarios.sample_scenarios import SCENARIOS
from storage import (
    clear_investigations,
    list_investigations,
    load_investigation,
    load_record,
    log_admin_event,
    recent_admin_events,
    stats,
)
from theme import metric_row, page_title

MAX_ATTEMPTS = 5
DEFAULT_EMAIL = "admin@ciares.local"

TABS = (
    "Dashboard",
    "Knowledge base",
    "Inference engine",
    "Decision engine",
    "Audit",
    "System map",
)


# ---------------------------------------------------------------------------
# Authentication gate (single administrator, session level)
# ---------------------------------------------------------------------------
def _auth_section() -> dict[str, Any]:
    try:
        section = st.secrets.get("auth", {})
    except Exception:  # no secrets file configured
        return {}
    return dict(section) if section else {}


def _configured() -> bool:
    section = _auth_section()
    return bool(section.get("admin_password_hash") or section.get("admin_password"))


def _signed_in() -> bool:
    return bool(st.session_state.get("admin_ok"))


def _attempts() -> int:
    return int(st.session_state.get("admin_attempts", 0))


def _failure(email: str) -> None:
    st.session_state["admin_attempts"] = _attempts() + 1
    log_admin_event("login_fail", email or "(no email)")


def _success(email: str) -> None:
    st.session_state["admin_ok"] = True
    st.session_state["admin_email"] = email
    st.session_state["admin_since"] = datetime.now().isoformat(timespec="seconds")
    st.session_state["admin_attempts"] = 0
    log_admin_event("login_ok", email)


def sign_out() -> None:
    email = st.session_state.get("admin_email", "")
    st.session_state["admin_ok"] = False
    st.session_state.pop("admin_email", None)
    st.session_state.pop("admin_since", None)
    log_admin_event("logout", email)


def _login_form() -> None:
    st.markdown("### Administrator sign-in")
    st.caption(
        "This area exposes the knowledge base, the inference engine and the "
        "decision engine. It is not part of the public investigation portal."
    )

    if not _configured():
        st.warning(
            "No admin credential is configured. Add an [auth] section to "
            ".streamlit/secrets.toml (or the Streamlit Cloud app secrets)."
        )
        return

    if _attempts() >= MAX_ATTEMPTS:
        st.error("Sign-in is locked for this session after repeated failures.")
        return

    section = _auth_section()
    expected_email = str(section.get("admin_email", DEFAULT_EMAIL))
    stored_hash = section.get("admin_password_hash")
    stored_password = section.get("admin_password")

    with st.form("admin_login_form", clear_on_submit=False):
        email = st.text_input("Email", placeholder=expected_email, autocomplete="username")
        password = st.text_input(
            "Password", type="password", autocomplete="current-password"
        )
        submitted = st.form_submit_button("Sign in", type="primary")

    if not submitted:
        return

    if verify_credentials(
        email,
        password,
        stored_email=expected_email,
        stored_hash=stored_hash,
        stored_password=stored_password,
    ):
        _success(email.strip().lower())
        st.rerun()
    _failure(email.strip())
    st.error("Invalid credentials.")


def _account_bar() -> None:
    email = st.session_state.get("admin_email", "administrator")
    since = st.session_state.get("admin_since", "")
    left, right = st.columns([3, 1])
    left.caption(f"Signed in as **{email}**" + (f" · since {since}" if since else ""))
    if right.button("Sign out", use_container_width=True):
        sign_out()
        st.rerun()


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------
def _select_investigation(
    key: str,
) -> tuple[dict[str, Any] | None, Investigation | None, dict[str, Any] | None]:
    rows = list_investigations(limit=200)
    if not rows:
        st.info(
            "No investigations recorded yet. Run one from the public portal and it "
            "will appear here."
        )
        return None, None, None

    identifiers = [row["id"] for row in rows]
    labels = {
        row["id"]: (
            f"{row['id']} · {row['name']} · {row['created_at']} · "
            f"{row['findings']} finding(s)"
        )
        for row in rows
    }
    chosen = st.selectbox(
        "Investigation", identifiers, format_func=lambda item: labels[item], key=key
    )
    row = next(item for item in rows if item["id"] == chosen)
    return row, load_investigation(chosen), load_record(chosen)


# ---------------------------------------------------------------------------
# Tab 1 - Dashboard
# ---------------------------------------------------------------------------
def _dashboard() -> None:
    report = validate_catalogue(ALL_RULES)
    summary = stats()

    metric_row(
        [
            ("Investigations", summary["investigations"], "Records in the SQLite store"),
            ("Findings", summary["findings"], "Total findings across all runs"),
            ("Critical", summary["critical"], "Critical findings"),
            ("Approved actions", summary["approved"], "Recommendations accepted by an analyst"),
            ("Rules", len(ALL_RULES), "Registered IF-THEN rules"),
            ("Conditions", report.condition_count, "Logical conditions in the knowledge base"),
        ]
    )

    st.divider()
    left, right = st.columns(2)
    with left:
        st.markdown("#### Findings by severity")
        if summary["findings"]:
            st.bar_chart(
                pd.DataFrame(
                    {
                        "Severity": ["Critical", "High", "Medium", "Low"],
                        "Findings": [
                            summary["critical"],
                            summary["high"],
                            summary["medium"],
                            summary["low"],
                        ],
                    }
                ),
                x="Severity",
                y="Findings",
                height=240,
            )
        else:
            st.caption("No findings recorded yet.")

    with right:
        st.markdown("#### Findings by module")
        modules = summary.get("by_module", {})
        if modules:
            frame = pd.DataFrame(
                sorted(modules.items(), key=lambda item: -item[1]),
                columns=["Module", "Findings"],
            )
            st.bar_chart(frame, x="Module", y="Findings", height=240)
        else:
            st.caption("No findings recorded yet.")

    st.divider()
    left, right = st.columns([1.2, 1])
    with left:
        st.markdown("#### Knowledge base")
        st.dataframe(
            pd.DataFrame(module_summary()).rename(
                columns={"module": "Module", "rules": "Rules", "conditions": "Conditions"}
            ),
            hide_index=True,
        )
        status = "✅ catalogue valid" if report.ok else f"⚠️ {len(report.errors)} error(s)"
        st.caption(f"{report.summary()} · {status}")
        if report.errors:
            st.error("\n".join(f"- {error}" for error in report.errors))

    with right:
        st.markdown("#### Recent admin activity")
        events = recent_admin_events(limit=8)
        if events:
            st.dataframe(pd.DataFrame(events), hide_index=True)
        else:
            st.caption("No admin events recorded.")

    st.caption(
        "Storage note: records live in data/ciares.db. On Streamlit Community Cloud "
        "the filesystem is ephemeral, so records reset after a redeploy or a long sleep."
    )


# ---------------------------------------------------------------------------
# Tab 2 - Knowledge base
# ---------------------------------------------------------------------------
def _knowledge() -> None:
    report = validate_catalogue(ALL_RULES)

    metric_row(
        [
            ("Rules", len(ALL_RULES), "Manually authored IF-THEN rules"),
            ("Logical conditions", report.condition_count, "Assignment minimum is 50"),
            (
                "Distinct fact fields",
                report.distinct_condition_fields,
                "Unique facts referenced by conditions",
            ),
            ("Modules", len(MODULES), "Specialised cybersecurity areas"),
        ]
    )

    if report.errors:
        st.error(
            "Knowledge base validation failed:\n\n"
            + "\n".join(f"- {error}" for error in report.errors)
        )
    else:
        st.success(
            "Knowledge base structure is valid: unique IDs, conditions present, "
            "severities and sources approved."
        )
    st.caption(
        "A condition is one declarative triple (field, operator, value). A rule fires "
        "only when every condition is satisfied; Unknown never satisfies a condition."
    )

    tabs = st.tabs([f"{module} ({len(RULES_BY_MODULE[module])})" for module in MODULES])
    for tab, module in zip(tabs, MODULES):
        rules = RULES_BY_MODULE[module]
        with tab:
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

    st.divider()
    st.markdown("#### Condition inventory")
    st.dataframe(
        pd.DataFrame(report.inventory).rename(
            columns={
                "field": "Fact field",
                "conditions": "Conditions",
                "rules": "Rules using it",
            }
        ),
        hide_index=True,
    )


# ---------------------------------------------------------------------------
# Tab 3 - Inference engine
# ---------------------------------------------------------------------------
def _working_memory(record: dict[str, Any]) -> None:
    observations = record.get("observations", {})
    st.markdown("#### Observations")
    st.dataframe(
        pd.DataFrame(
            [
                {"Fact": key, "Value": str(value), "Source": "Observation"}
                for key, value in observations.items()
            ]
        ),
        hide_index=True,
    )

    derived = record.get("derived", [])
    st.markdown("#### Derived conclusions (with provenance)")
    if derived:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Fact": item["key"],
                        "Value": str(item.get("value", "True")),
                        "Derived by": item.get("rule_id") or "",
                        "Supporting facts": ", ".join(
                            f"{key}={value}" for key, value in item.get("supporting", [])
                        ),
                    }
                    for item in derived
                ]
            ),
            hide_index=True,
        )
    else:
        st.caption("No derived-fact provenance stored for this record.")


def _inference() -> None:
    st.caption(
        "Forward chaining fires one rule per cycle and records the real reasoning "
        "order. Activation keys stop the same rule firing twice on identical evidence."
    )

    _row, investigation, record = _select_investigation("admin_inference")
    if investigation is None or record is None:
        return

    engine = ExplanationEngine()
    st.markdown(
        f"**{investigation.id}** · {investigation.name} · "
        f"{len(investigation.activations)} activation(s) · "
        f"{investigation.terminated_reason}"
    )

    tabs = st.tabs(
        ["Activation sequence", "Justification", "Working memory", "Reasoning log"]
    )

    with tabs[0]:
        if investigation.activations:
            st.dataframe(
                pd.DataFrame(engine.activation_rows(investigation)),
                hide_index=True,
                column_config={"#": st.column_config.NumberColumn(width="small")},
            )
        else:
            st.info("No rule activated for this investigation.")

    with tabs[1]:
        if not investigation.activations:
            st.info("Nothing to justify yet.")
        else:
            identifiers = [activation.rule.id for activation in investigation.activations]
            chosen = st.selectbox("Rule activation", identifiers, key="admin_justify_rule")
            activation = next(
                item for item in investigation.activations if item.rule.id == chosen
            )
            st.markdown(engine.justification_markdown(activation))
            st.dataframe(
                pd.DataFrame(engine.justification(activation)["conditions"]),
                hide_index=True,
            )

    with tabs[2]:
        _working_memory(record)

    with tabs[3]:
        st.dataframe(
            pd.DataFrame(engine.trace_rows(investigation)),
            hide_index=True,
            column_config={
                "Step": st.column_config.NumberColumn(width="small"),
                "Event": st.column_config.TextColumn(width="small"),
                "Detail": st.column_config.TextColumn(width="large"),
            },
        )

    st.divider()
    st.download_button(
        "Download investigation report (Markdown)",
        data=engine.markdown_report(investigation).encode("utf-8"),
        file_name=f"{investigation.id}.md",
        mime="text/markdown",
    )


# ---------------------------------------------------------------------------
# Tab 4 - Decision engine
# ---------------------------------------------------------------------------
DECISION_RULES = (
    "A response is recommended only when the rule behind a finding asks for it.",
    "Identical actions are collapsed into one recommendation.",
    "Recovery is deferred while a containment action is still open.",
    "Recommendations are ordered by response phase, then by declared priority.",
    "The analyst approves the list; CIARES itself executes nothing.",
)


def _decision() -> None:
    page_title(
        "Decision engine",
        "The inference engine answers what is happening; this layer decides what "
        "should be done about it.",
    )

    st.markdown("#### Decision rules applied")
    for index, rule in enumerate(DECISION_RULES, start=1):
        st.markdown(f"{index}. {rule}")

    st.divider()
    _row, investigation, _record = _select_investigation("admin_decision")
    if investigation is None:
        return

    engine = ExplanationEngine()
    st.markdown("#### Recommendations")
    if investigation.actions:
        st.dataframe(
            pd.DataFrame(engine.action_rows(investigation)),
            hide_index=True,
        )
        if investigation.approved_at:
            st.caption(f"Approved by the analyst at {investigation.approved_at}.")
        else:
            st.caption("Not approved yet.")
    else:
        st.caption("No action was recommended for this investigation.")

    st.divider()
    st.markdown("#### Action catalogue")
    st.caption(
        "Every response CIARES can recommend, with the phase, urgency and the reason "
        "shown to the analyst."
    )
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Action key": spec.key,
                    "Label": spec.label,
                    "Phase": spec.phase.value,
                    "Priority": spec.priority,
                    "What it does": spec.description,
                }
                for spec in sorted(
                    ACTION_LIBRARY.values(), key=lambda item: (item.phase.order, item.priority)
                )
            ]
        ),
        hide_index=True,
    )


# ---------------------------------------------------------------------------
# Tab 5 - Audit
# ---------------------------------------------------------------------------
def _audit_investigations() -> None:
    left, middle, right = st.columns(3)
    source_label = left.selectbox("Source", ["all", "manual", "scenario"], key="audit_source")
    scenario_options = ["all"] + [scenario.id for scenario in SCENARIOS]
    scenario_label = middle.selectbox("Scenario", scenario_options, key="audit_scenario")
    limit = right.slider("Maximum rows", 10, 200, 50, step=10, key="audit_limit")

    rows = list_investigations(
        limit=limit,
        source=None if source_label == "all" else source_label,
        scenario_id=None if scenario_label == "all" else scenario_label,
    )

    if not rows:
        st.info("No records match the current filters.")
        return

    st.dataframe(pd.DataFrame(rows), hide_index=True)

    st.divider()
    st.markdown("#### Inspect a record")
    identifiers = [row["id"] for row in rows]
    labels = {
        row["id"]: f"{row['id']} · {row['name']} · {row['created_at']}" for row in rows
    }
    chosen = st.selectbox(
        "Investigation", identifiers, format_func=lambda item: labels[item], key="audit_pick"
    )
    investigation = load_investigation(chosen)
    record = load_record(chosen)
    if investigation is None or record is None:
        st.error("The selected record could not be loaded.")
        return

    engine = ExplanationEngine()
    tabs = st.tabs(["Findings", "Observations", "Activations", "Recommendations"])
    with tabs[0]:
        if investigation.findings:
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Finding": finding.label,
                            "Severity": finding.severity.value,
                            "Module": finding.module,
                            "Rules": ", ".join(finding.rule_ids),
                        }
                        for finding in investigation.findings
                    ]
                ),
                hide_index=True,
            )
        else:
            st.caption("No findings in this record.")
    with tabs[1]:
        observations = record.get("observations", {})
        st.dataframe(
            pd.DataFrame(
                [{"Fact": key, "Value": str(value)} for key, value in observations.items()]
            ),
            hide_index=True,
        )
    with tabs[2]:
        st.dataframe(pd.DataFrame(engine.activation_rows(investigation)), hide_index=True)
    with tabs[3]:
        st.dataframe(pd.DataFrame(engine.action_rows(investigation)), hide_index=True)

    st.divider()
    left, right = st.columns(2)
    left.download_button(
        "Download record (JSON)",
        data=json.dumps(record, indent=2).encode("utf-8"),
        file_name=f"{investigation.id}.json",
        mime="application/json",
    )
    right.download_button(
        "Download summary (CSV)",
        data=pd.DataFrame(rows).to_csv(index=False).encode("utf-8"),
        file_name="ciares_investigations.csv",
        mime="text/csv",
    )

    st.divider()
    with st.expander("Danger zone"):
        confirmed = st.checkbox(
            "I understand this deletes every stored investigation.",
            key="audit_confirm_clear",
        )
        if st.button("Clear all records", disabled=not confirmed):
            clear_investigations()
            log_admin_event("clear", "all investigation records deleted")
            st.session_state["investigation"] = None
            st.rerun()


def _audit() -> None:
    st.caption(
        "A record is written after every investigation and updated when the analyst "
        "approves a plan. Records are session-independent while the container is awake."
    )
    tabs = st.tabs(["Investigations", "Admin events"])
    with tabs[0]:
        _audit_investigations()
    with tabs[1]:
        events = recent_admin_events(limit=50)
        if events:
            st.dataframe(pd.DataFrame(events), hide_index=True)
        else:
            st.caption("No admin events recorded yet.")


# ---------------------------------------------------------------------------
# Tab 6 - System map
# ---------------------------------------------------------------------------
def _system_map() -> None:
    st.caption(
        "A reading guide to the codebase, written for the questions 'what does this "
        "function do?' and 'what happens if I delete it?'."
    )
    document = PROJECT_ROOT / "docs" / "system_map.md"
    if not document.exists():
        st.warning(f"System map not found at {document}.")
        return
    st.markdown(document.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def render() -> None:
    if not _signed_in():
        _login_form()
        return

    page_title(
        "Administration",
        "The internal view of CIARES: the knowledge base, the inference engine, the "
        "decision engine and the audit trail. The public portal never exposes this.",
    )
    _account_bar()
    st.divider()

    tabs = st.tabs(list(TABS))
    renderers = (_dashboard, _knowledge, _inference, _decision, _audit, _system_map)
    for tab, renderer in zip(tabs, renderers):
        with tab:
            renderer()
