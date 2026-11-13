"""
Presentation helpers: Poppins, page header, cards, metrics and the threat meter.

Everything visual lives here so ``app.py`` and ``admin.py`` only describe *what*
to show. The font is applied to text elements rather than ``*`` so Streamlit's
Material icon font keeps working.
"""

from __future__ import annotations

from typing import Any, Sequence

import streamlit as st

from config import APP_NAME, APP_TAGLINE
from engine.models import Severity

SEVERITY_COLOUR: dict[Severity, str] = {
    Severity.CRITICAL: "#ef4444",
    Severity.HIGH: "#f97316",
    Severity.MEDIUM: "#eab308",
    Severity.LOW: "#22c55e",
}

# Emoji icons for the sidebar and the cards.
SECTION_ICONS: dict[str, str] = {
    "Home": "🏠",
    "Investigate": "🔍",
    "Scenarios": "🧪",
    "Results": "📄",
}

MODULE_ICONS: dict[str, str] = {
    "Authentication & Account Security": "🔑",
    "Malware & Process Security": "🦠",
    "Network Security": "🌐",
    "Data Security & Protection": "🗄️",
    "Privilege & Security Policy": "🛡️",
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap');

html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"],
[data-testid="stMarkdownContainer"], [data-testid="stMetricValue"],
[data-testid="stMetricLabel"], [data-testid="stWidgetLabel"],
p, h1, h2, h3, h4, h5, h6, li, label, button, input, textarea, select {
    font-family: 'Poppins', 'Segoe UI', sans-serif !important;
}

/* Sidebar menu labels are emojis: keep them readable, not microscopic. */
[data-testid="stSidebar"] [role="radiogroup"] label p {font-size: 1.1rem;}
[data-testid="stSidebar"] [role="radiogroup"] label {line-height: 1.9;}

/* Never restyle the icon font, or arrows turn into words. */
[data-testid="stIconMaterial"], .material-symbols-rounded, .material-icons {
    font-family: 'Material Symbols Rounded' !important;
}

/* Streamlit's own page list is hidden: the sidebar radio is the only menu. */
[data-testid="stSidebarNav"] {display: none !important;}

html {scroll-padding-top: 4.4rem;}

/* The header floats over the content: keep it transparent and give the page
   enough top padding that the first card is never clipped by it. */
[data-testid="stHeader"] {background: transparent;}
.block-container {padding-top: 4.2rem; max-width: 1150px;}

.cihares-hero {
    background: linear-gradient(120deg, rgba(34,211,238,0.16), rgba(59,130,246,0.05));
    border: 1px solid rgba(34,211,238,0.25);
    border-radius: 18px;
    padding: 26px 30px;
    margin-bottom: 22px;
}
.cihares-hero h1 {margin: 0 0 2px 0; font-size: 2.4rem; letter-spacing: 0.04em;}
.cihares-sub {font-size: 1rem; color: #e2e8f0;}
.cihares-kicker {
    font-size: 0.72rem; letter-spacing: 0.18em; text-transform: uppercase;
    color: #22d3ee; margin-top: 10px;
}
.cihares-desc {font-size: 0.88rem; color: #94a3b8; margin-top: 8px; max-width: 900px;}

.cihares-grid {
    display: grid;
    gap: 16px;
    margin: 4px 0 22px 0;
}
@media (max-width: 820px) {
    .cihares-grid {grid-template-columns: 1fr !important;}
}
.cihares-card {
    background: rgba(20,29,47,0.75);
    border: 1px solid rgba(148,163,184,0.16);
    border-radius: 14px;
    padding: 16px 18px;
    height: 100%;
}
.cihares-card h4 {margin: 0 0 6px 0; font-size: 0.95rem;}
.cihares-card p {margin: 0; font-size: 0.82rem; color: #94a3b8;}
.cihares-ic {
    font-size: 1.1rem;
    line-height: 1;
    margin-right: 7px;
    vertical-align: -2px;
    font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}

[data-testid="stMetric"] {
    background: rgba(20,29,47,0.85);
    border: 1px solid rgba(148,163,184,0.16);
    border-radius: 14px;
    padding: 14px 16px;
}
[data-testid="stMetricLabel"] p {font-size: 0.76rem; letter-spacing: 0.06em; text-transform: uppercase;}

.cihares-threat {
    background: rgba(20,29,47,0.85);
    border: 1px solid rgba(148,163,184,0.18);
    border-radius: 16px;
    padding: 18px 22px;
    margin: 6px 0 18px 0;
}
.cihares-threat-top {display: flex; justify-content: space-between; align-items: baseline;}
.cihares-threat-label {font-size: 0.72rem; letter-spacing: 0.16em; text-transform: uppercase; color: #94a3b8;}
.cihares-threat-score {font-size: 1.9rem; font-weight: 700;}
.cihares-threat-score span {font-size: 0.9rem; color: #64748b; font-weight: 500;}
.cihares-threat-track {
    background: rgba(148,163,184,0.18);
    border-radius: 999px;
    height: 10px;
    margin: 10px 0 12px 0;
    overflow: hidden;
}
.cihares-threat-fill {height: 100%; border-radius: 999px;}
.cihares-threat-sentence {margin: 0; font-size: 0.95rem; color: #e2e8f0;}

.cihares-finding {border-left: 3px solid #64748b; padding-left: 14px; margin-bottom: 16px;}
.cihares-finding h4 {margin: 0 0 2px 0;}
.cihares-finding p {margin: 4px 0 0 0; color: #cbd5e1; font-size: 0.92rem;}
.cihares-chip {
    display: inline-block; font-size: 0.7rem; letter-spacing: 0.08em;
    text-transform: uppercase; padding: 2px 8px; border-radius: 999px;
    border: 1px solid currentColor; margin-left: 8px;
}
.cihares-foot {font-size: 0.76rem; color: #64748b; margin-top: 28px;}
</style>
"""


def apply_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def hero(subtitle: str | None = None) -> None:
    st.markdown(
        f"""
        <div class="cihares-hero">
            <h1>{APP_NAME}</h1>
            <div class="cihares-sub">{subtitle or APP_TAGLINE}</div>
            <div class="cihares-kicker">Rule-based Expert System</div>
            <div class="cihares-desc">
                Describe what was observed, read the diagnosis in plain language,
                approve the recommendations you agree with, and receive a written
                response plan.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_title(title: str, subtitle: str | None = None) -> None:
    st.subheader(title)
    if subtitle:
        st.caption(subtitle)


def card(title: str, body: str, icon: str | None = None) -> str:
    badge = (
        f'<span class="cihares-ic">{icon}</span>'
        if icon
        else ""
    )
    return f'<div class="cihares-card"><h4>{badge}{title}</h4><p>{body}</p></div>'


def card_grid(
    items: Sequence[tuple[str, str, str]],
    columns: int = 3,
) -> str:
    """Render ``(icon, title, body)`` triples as one evenly spaced CSS grid.

    A single grid (rather than nested ``st.columns``) keeps the gap between
    rows and stops cards from touching when the item count is not a multiple
    of the column count.
    """
    cells = "".join(card(title, body, icon) for icon, title, body in items)
    return (
        f'<div class="cihares-grid" '
        f'style="grid-template-columns:repeat({columns}, minmax(0, 1fr));">'
        f"{cells}</div>"
    )


def metric_row(items: Sequence[tuple[str, Any, str]]) -> None:
    for start in range(0, len(items), 3):
        columns = st.columns(3)
        for column, (label, value, help_text) in zip(columns, items[start : start + 3]):
            column.metric(label, value, help=help_text)


def threat_meter(score: int, sentence: str, severity: Severity | None) -> None:
    colour = SEVERITY_COLOUR.get(severity, "#38bdf8") if severity else "#38bdf8"
    st.markdown(
        f"""
        <div class="cihares-threat">
            <div class="cihares-threat-top">
                <span class="cihares-threat-label">Threat level</span>
                <span class="cihares-threat-score" style="color:{colour}">{score}<span>/100</span></span>
            </div>
            <div class="cihares-threat-track">
                <div class="cihares-threat-fill" style="width:{max(0, min(score, 100))}%; background:{colour};"></div>
            </div>
            <p class="cihares-threat-sentence">{sentence}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def severity_chip(severity: Severity) -> str:
    colour = SEVERITY_COLOUR.get(severity, "#94a3b8")
    return (
        f'<span class="cihares-chip" style="color:{colour}">{severity.value}</span>'
    )


def footer() -> None:
    st.markdown(
        f'<div class="cihares-foot">{APP_NAME} · forward chaining · '
        f"decision support for a human analyst · Python + Streamlit</div>",
        unsafe_allow_html=True,
    )
