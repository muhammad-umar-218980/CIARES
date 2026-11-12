"""Shared presentation helpers: theme, headings, metrics and small tables."""

from __future__ import annotations

from typing import Any, Iterable, Sequence

import pandas as pd
import streamlit as st

from config import APP_DESCRIPTION, APP_NAME, APP_TAGLINE, APP_VERSION
from engine.models import Finding, Severity

CSS = """
<style>
.block-container {padding-top: 1.6rem; max-width: 1300px;}
.cihares-hero {
    background: linear-gradient(120deg, rgba(34,211,238,0.16), rgba(59,130,246,0.05));
    border: 1px solid rgba(34,211,238,0.25);
    border-radius: 18px;
    padding: 26px 30px;
    margin-bottom: 20px;
}
.cihares-kicker {font-size: 0.75rem; letter-spacing: 0.18em; text-transform: uppercase; color: #22d3ee;}
.cihares-hero h1 {margin: 6px 0 2px 0; font-size: 2.5rem; letter-spacing: 0.04em;}
.cihares-sub {font-size: 1.02rem; color: #e2e8f0;}
.cihares-desc {font-size: 0.9rem; color: #94a3b8; margin-top: 8px; max-width: 900px;}
.cihares-card {
    background: rgba(20,29,47,0.75);
    border: 1px solid rgba(148,163,184,0.16);
    border-radius: 14px;
    padding: 16px 18px;
    height: 100%;
}
.cihares-card h4 {margin: 0 0 6px 0; font-size: 0.95rem;}
.cihares-card p {margin: 0; font-size: 0.82rem; color: #94a3b8;}
[data-testid="stMetric"] {
    background: rgba(20,29,47,0.85);
    border: 1px solid rgba(148,163,184,0.16);
    border-radius: 14px;
    padding: 14px 16px;
}
[data-testid="stMetricLabel"] p {font-size: 0.78rem; letter-spacing: 0.06em; text-transform: uppercase;}
h2, h3 {letter-spacing: 0.01em;}
.cihares-foot {font-size: 0.78rem; color: #64748b; margin-top: 26px;}
/* The admin portal is reachable only by typing /admin: no nav entry. */
[data-testid="stSidebarNav"] a[href$="/admin"],
[data-testid="stSidebarNavLink"][href$="/admin"] {display: none !important;}
</style>
"""


def apply_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def hero(subtitle: str | None = None) -> None:
    st.markdown(
        f"""
        <div class="cihares-hero">
            <div class="cihares-kicker">Rule-based Expert System · v{APP_VERSION}</div>
            <h1>{APP_NAME}</h1>
            <div class="cihares-sub">{subtitle or APP_TAGLINE}</div>
            <div class="cihares-desc">{APP_DESCRIPTION}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_title(title: str, subtitle: str | None = None) -> None:
    st.subheader(title)
    if subtitle:
        st.caption(subtitle)


def card(title: str, body: str) -> str:
    return (
        f'<div class="cihares-card"><h4>{title}</h4><p>{body}</p></div>'
    )


def metric_row(items: Sequence[tuple[str, Any, str]]) -> None:
    """Three metrics per row so long labels are never truncated."""
    for start in range(0, len(items), 3):
        columns = st.columns(3)
        for column, (label, value, help_text) in zip(columns, items[start : start + 3]):
            column.metric(label, value, help=help_text)


def severity_dataframe(findings: Iterable[Finding]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Finding": finding.label,
                "Severity": finding.severity.value,
                "Module": finding.module,
                "Rules": ", ".join(finding.rule_ids),
                "Recommended response": finding.recommended_action or "—",
            }
            for finding in findings
        ]
    )


def severity_counts(findings: Sequence[Finding]) -> dict[str, int]:
    counts = {severity.value: 0 for severity in Severity}
    for finding in findings:
        counts[finding.severity.value] += 1
    return counts


def severity_chart(findings: Sequence[Finding], height: int = 220) -> None:
    """Bar chart of findings by severity; shows an empty state instead of a blank box."""
    if not findings:
        st.caption("No findings to chart.")
        return
    counts = severity_counts(findings)
    frame = pd.DataFrame(
        {
            "Severity": ["Critical", "High", "Medium", "Low"],
            "Findings": [counts["Critical"], counts["High"], counts["Medium"], counts["Low"]],
        }
    )
    st.bar_chart(frame, x="Severity", y="Findings", height=height)


def severity_badge(findings: Sequence[Finding]) -> str:
    """One-line threat summary used above the results table."""
    counts = severity_counts(findings)
    parts = [f"{counts['Critical']} critical", f"{counts['High']} high"]
    parts.append(f"{counts['Medium']} medium")
    parts.append(f"{counts['Low']} low")
    return " · ".join(parts)


def footer() -> None:
    st.markdown(
        f'<div class="cihares-foot">{APP_NAME} v{APP_VERSION} · forward chaining · '
        f"responses act on a simulated environment only · Python + Streamlit</div>",
        unsafe_allow_html=True,
    )


def simulation_disclaimer() -> None:
    st.caption(
        "Responses are executed against CIARES's internal simulated environment. "
        "No real account, host, process or network is contacted or modified."
    )
