"""
Build the CIARES technical/code-explanation PDF.

Pipeline
--------
1. Read ``docs/code_explanation.md`` and replace data placeholders with tables
   generated from the running project (rules, conditions, scenarios, tests).
2. Convert Markdown to HTML with Python-Markdown.
3. Wrap the body in a print stylesheet, generate a cover page and a table of
   contents, and embed the UI screenshots as base64 PNGs.
4. Print the cover and body with headless Chromium (Playwright/Patchright) and
   merge them with pypdf, so page numbers start on the first content page.

Usage
-----
    python scripts/build_pdf.py

Outputs
-------
    CIARES_Code_Explanation.pdf   (repository root)
    docs/code_explanation.html    (intermediate, reproducible)
"""

from __future__ import annotations

import base64
import html
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import markdown  # noqa: E402
from pypdf import PdfReader, PdfWriter  # noqa: E402

from config import THRESHOLDS  # noqa: E402
from engine.decision_engine import ACTION_LIBRARY  # noqa: E402
from engine.explanation_engine import ExplanationEngine  # noqa: E402
from engine.pipeline import run_investigation  # noqa: E402
from knowledge_base.knowledge_acquisition import validate_catalogue  # noqa: E402
from knowledge_base.rule_registry import ALL_RULES, MODULES, RULES_BY_MODULE  # noqa: E402
from scenarios.sample_scenarios import SCENARIOS  # noqa: E402
from simulation import ALL_ACTIONS, available_actions  # noqa: E402

DOC = ROOT / "docs" / "code_explanation.md"
HTML_OUT = ROOT / "docs" / "code_explanation.html"
PDF_OUT = ROOT / "CIARES_Code_Explanation.pdf"
SHOTS = ROOT / "docs" / "screenshots"
NODE = ROOT / "scripts" / "print_pdf.cjs"

REPORT = validate_catalogue(ALL_RULES)
TODAY = date.today().strftime("%B %Y")


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------
def md_cell(value: object) -> str:
    """Escape a value for a Markdown table cell."""
    text = str(value).replace("|", "\\|").replace("\n", " ").strip()
    return text or "—"


def table(headers: list[str], rows: list[list[object]], align: list[str] | None = None) -> str:
    head = "| " + " | ".join(headers) + " |"
    if align:
        sep = "| " + " | ".join(align) + " |"
    else:
        sep = "|" + "|".join(["---"] * len(headers)) + "|"
    body = ["| " + " | ".join(md_cell(cell) for cell in row) + " |" for row in rows]
    return "\n".join([head, sep, *body])


def severity_of(rules) -> dict[str, int]:
    counts: dict[str, int] = {}
    for rule in rules:
        counts[rule.severity.value] = counts.get(rule.severity.value, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# Dynamic content
# ---------------------------------------------------------------------------
def build_module_table() -> str:
    rows = []
    for module in MODULES:
        rules = RULES_BY_MODULE[module]
        actionable = sum(1 for rule in rules if rule.is_actionable)
        rows.append(
            [module, len(rules), sum(len(rule.conditions) for rule in rules), actionable]
        )
    return table(["Module", "Rules", "Logical conditions", "Actionable rules"], rows,
                 ["---", "---:", "---:", "---:"])


def build_severity_table() -> str:
    authored = severity_of(ALL_RULES)
    scenario_counts: dict[str, int] = {}
    for scenario in SCENARIOS:
        investigation = run_investigation(
            scenario.observations, scenario.entities, scenario.name, scenario_id=scenario.id
        )
        for finding in investigation.findings:
            scenario_counts[finding.severity.value] = (
                scenario_counts.get(finding.severity.value, 0) + 1
            )
    rows = []
    for severity in ("Critical", "High", "Medium", "Low"):
        rows.append([severity, authored.get(severity, 0), scenario_counts.get(severity, 0)])
    rows.append(["Total", len(ALL_RULES), sum(scenario_counts.values())])
    return table(["Severity", "Authored rules", "Findings across the six scenarios"], rows,
                 ["---", "---:", "---:"])


def build_threshold_table() -> str:
    hints = {
        "failed_login_attempts": "failed login attempts",
        "concurrent_sessions": "simultaneous sessions",
        "mfa_failures": "MFA verification failures",
        "outbound_traffic_mb": "megabytes of outbound traffic",
        "transfer_volume_mb": "megabytes transferred",
        "download_count": "files downloaded",
        "connection_attempts": "connection attempts",
        "denied_requests": "denied requests",
    }
    rows = []
    for key, value in THRESHOLDS.items():
        field = "denied_request_count" if key == "denied_requests" else key
        users = [rule.id for rule in ALL_RULES if any(c.field == field for c in rule.conditions)]
        rows.append([f"`{key}`", value, hints.get(key, ""), ", ".join(users)])
    return table(["Fact field", "Assumed threshold", "Measured quantity", "Rules using it"], rows)


def build_action_table() -> str:
    labels = available_actions()
    rows = []
    for key, spec in ACTION_LIBRARY.items():
        required = ", ".join(sorted(spec.required_values)) if spec.required_values else "any"
        rows.append(
            [
                f"`{key}`",
                labels.get(key, spec.label),
                spec.phase.value,
                spec.priority,
                spec.target_type,
                f"`{spec.required_field}` = {required}",
                spec.description,
            ]
        )
    return table(
        ["Action key", "Label", "Phase", "Priority", "Target", "Required state", "Purpose"],
        rows,
    )


def build_scenario_table() -> str:
    rows = []
    for scenario in SCENARIOS:
        rows.append(
            [
                scenario.id,
                scenario.name.replace(" Investigation", ""),
                len(scenario.observations),
                len(scenario.entities),
                len(scenario.expected_findings),
            ]
        )
    return table(
        ["ID", "Focus", "Observations supplied", "Entity IDs", "Expected findings"],
        rows,
        ["---", "---", "---:", "---:", "---:"],
    )


def build_scenario_result_table() -> str:
    rows = []
    totals = [0, 0, 0, 0, 0]
    for scenario in SCENARIOS:
        investigation = run_investigation(
            scenario.observations, scenario.entities, scenario.name, scenario_id=scenario.id
        )
        proposed = len(investigation.actions)
        executable = sum(1 for action in investigation.actions if action.executable)
        skipped = sum(1 for action in investigation.actions if action.status == "Skipped")
        totals[0] += len(investigation.activations)
        totals[1] += len(investigation.findings)
        totals[2] += proposed
        totals[3] += executable
        totals[4] += skipped
        rows.append(
            [
                scenario.id,
                len(investigation.activations),
                len(investigation.findings),
                proposed,
                executable,
                skipped,
                investigation.terminated_reason,
            ]
        )
    rows.append(
        ["Total", totals[0], totals[1], totals[2], totals[3], totals[4], "all fixed points"]
    )
    return table(
        ["Scenario", "Activations", "Findings", "Proposed actions", "Executable", "Skipped", "Termination"],
        rows,
        ["---", "---:", "---:", "---:", "---:", "---:", "---"],
    )


def scn001():
    scenario = next(item for item in SCENARIOS if item.id == "SCN-001")
    return run_investigation(
        scenario.observations, scenario.entities, scenario.name, scenario_id=scenario.id
    )


def build_scn001_trace() -> str:
    investigation = scn001()
    rows = [
        [
            activation.sequence,
            f"`{activation.rule.id}`",
            activation.rule.name,
            activation.conclusion_label,
            activation.rule.severity.value,
            "Yes" if activation.inserted_new_fact else "Already known",
        ]
        for activation in investigation.activations
    ]
    return table(
        ["#", "Rule", "Name", "Conclusion", "Severity", "New fact"], rows,
        ["---:", "---", "---", "---", "---", "---"],
    )


def build_scn001_memory() -> str:
    investigation = scn001()
    memory = investigation.memory  # type: ignore[attr-defined]
    rows = [
        [
            f"`{fact.key}`",
            fact.state,
            fact.rule_id or fact.source,
            ", ".join(f"`{key}`" for key, _ in fact.supporting),
        ]
        for fact in memory.derived_facts()
    ]
    return table(["Derived fact", "Value", "Derived by", "Supporting facts"], rows)


def build_scn001_findings() -> str:
    investigation = scn001()
    rows = [
        [
            finding.label,
            finding.severity.value,
            finding.module,
            ", ".join(f"`{rule_id}`" for rule_id in finding.rule_ids),
            f"`{finding.recommended_action}`" if finding.recommended_action else "—",
        ]
        for finding in investigation.findings
    ]
    return table(["Finding", "Severity", "Module", "Rules", "Response"], rows)


def build_scn001_justification() -> str:
    investigation = scn001()
    activation = next(
        item for item in investigation.activations if item.rule.id == "AUTH-04"
    )
    data = ExplanationEngine().justification(activation)
    rows = [
        [
            row["Condition"],
            f"`{row['Field']}`",
            row["Operator"],
            row["Expected"],
            row["Observed"],
            row["Status"],
        ]
        for row in data["conditions"]
    ]
    return table(
        ["Condition", "Field", "Operator", "Expected", "Observed", "Status"], rows
    )


def build_rule_catalogue() -> str:
    parts: list[str] = []
    for module in MODULES:
        parts.append(f"### {module}")
        rows = []
        for rule in RULES_BY_MODULE[module]:
            rows.append(
                [
                    f"`{rule.id}`",
                    rule.name,
                    rule.describe_conditions(),
                    f"`{rule.conclusion_key}`",
                    rule.severity.value,
                    f"`{rule.recommended_action}`" if rule.recommended_action else "—",
                    rule.source,
                ]
            )
        parts.append(
            table(
                ["ID", "Rule", "IF", "THEN", "Severity", "Response", "Source"], rows
            )
        )
        parts.append("")
    return "\n".join(parts)


def build_condition_inventory() -> str:
    rows = [
        [f"`{item['field']}`", item["conditions"], item["rules"]]
        for item in REPORT.inventory
    ]
    return table(
        ["Fact field", "Conditions referencing it", "Distinct rules using it"],
        rows,
        ["---", "---:", "---:"],
    )


def build_file_tree() -> str:
    excluded = {".git", ".pytest_cache", "__pycache__", ".venv", "venv", ".idea", ".vscode"}
    collapsed = {"docs/screenshots"}

    def entries(path: Path) -> list[Path]:
        items = [item for item in path.iterdir() if item.name not in excluded]
        return sorted(items, key=lambda item: (item.is_file(), item.name.lower()))

    def walk(path: Path, prefix: str = "") -> list[str]:
        lines: list[str] = []
        items = entries(path)
        for index, item in enumerate(items):
            last = index == len(items) - 1
            connector = "└── " if last else "├── "
            relative = item.relative_to(ROOT).as_posix()
            if relative in collapsed:
                count = len(list(item.glob("*.png")))
                lines.append(f"{prefix}{connector}{item.name}/")
                lines.append(f"{prefix}{'    ' if last else '│   '}└── {count} PNG evidence files")
                continue
            suffix = "/" if item.is_dir() else ""
            lines.append(f"{prefix}{connector}{item.name}{suffix}")
            if item.is_dir():
                extension = "    " if last else "│   "
                lines.extend(walk(item, prefix + extension))
        return lines

    return "```text\nCIARES/\n" + "\n".join(walk(ROOT)) + "\n```"


PURPOSES = {
    "app.py": "Streamlit entry point; seven pages; session state; calls the pipeline",
    "config.py": "Identity, paths, threshold assumptions, approved sources, working hours",
    "requirements.txt": "Runtime dependencies (Streamlit, pandas, pytest)",
    "README.md": "Installation, architecture, usage, limitations",
    "CIARES.txt": "Original assignment specification and design brief",
    "engine/__init__.py": "Package exports",
    "engine/models.py": "Data structures and three-valued condition evaluation",
    "engine/working_memory.py": "Facts, provenance, contradictions and trace",
    "engine/inference_engine.py": "Forward chaining, activation keys, fixed point",
    "engine/decision_engine.py": "Action library, target/state validation, ordering",
    "engine/pipeline.py": "Single end-to-end investigation pipeline",
    "engine/explanation_engine.py": "Trace, justification and action explanations",
    "knowledge_base/__init__.py": "Package exports",
    "knowledge_base/authentication.py": "AUTH-01 … AUTH-12",
    "knowledge_base/malware.py": "MAL-01 … MAL-12",
    "knowledge_base/network.py": "NET-01 … NET-12",
    "knowledge_base/data_security.py": "DATA-01 … DATA-12",
    "knowledge_base/security_policy.py": "POL-01 … POL-12",
    "knowledge_base/rule_registry.py": "Assembles ALL_RULES and module summaries",
    "knowledge_base/knowledge_acquisition.py": "Rule validation, counts, condition inventory",
    "simulation/__init__.py": "Action dispatch, available actions, execute()",
    "simulation/environment.py": "Simulated entities and guarded state transitions",
    "simulation/account_actions.py": "Account, session and permission actions",
    "simulation/network_actions.py": "Connection, destination and endpoint actions",
    "simulation/process_actions.py": "Process isolation, termination and quarantine",
    "simulation/data_policy_actions.py": "Transfer, data-access and permission actions",
    "scenarios/__init__.py": "Package exports",
    "scenarios/sample_scenarios.py": "SCN-001 … SCN-006 and expected findings",
    "tests/conftest.py": "Adds the project root to sys.path",
    "tests/test_rules.py": "Rule semantics and catalogue integrity",
    "tests/test_inference.py": "Chaining, termination, activation keys, provenance",
    "tests/test_decisions.py": "Target validation, conflicts, ordering",
    "tests/test_simulation.py": "State transitions and execution guards",
    "tests/test_scenarios.py": "Six end-to-end scenarios",
    "tests/test_coverage.py": "60-rule reachability and completeness guards",
    "docs/rule_catalogue.md": "All 60 rules with conditions and sources",
    "docs/rule_sources.md": "Reference mapping for every rule",
    "docs/technical_design.md": "Implementation design notes",
    "docs/demo_guide.md": "UI-only demonstration and viva script",
    "docs/code_explanation.md": "Source of this PDF",
    "scripts/build_pdf.py": "Builds this document from live project data",
    "scripts/print_pdf.cjs": "Headless Chromium print-to-PDF",
    "scripts/capture_screenshots.mjs": "Captures the UI evidence screenshots",
    ".streamlit/config.toml": "Streamlit theme and server settings",
}


def build_file_table() -> str:
    rows = []
    for path in sorted(
        (item for item in ROOT.rglob("*") if item.is_file()),
        key=lambda item: item.relative_to(ROOT).as_posix().lower(),
    ):
        relative = path.relative_to(ROOT).as_posix()
        if any(part in {".git", "__pycache__", ".pytest_cache"} for part in path.parts):
            continue
        if relative.startswith("data/") or relative.startswith("docs/screenshots/"):
            continue
        if path.suffix not in {".py", ".md", ".txt", ".toml", ".cjs", ".mjs"}:
            continue
        lines = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
        rows.append([f"`{relative}`", lines, PURPOSES.get(relative, "—")])
    return table(["Path", "Lines", "Responsibility"], rows, ["---", "---:", "---"])


def build_test_table() -> str:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    counts: dict[str, int] = {}
    for line in result.stdout.splitlines():
        if "::" in line:
            filename = line.split("::", 1)[0].strip()
            counts[filename] = counts.get(filename, 0) + 1
    purposes = {
        "tests/test_rules.py": "Thresholds, Unknown vs False, corroboration, condition semantics",
        "tests/test_inference.py": "Chaining order, fixed point, no re-fire, provenance, contradictions",
        "tests/test_decisions.py": "Target/state validation, duplicates, containment/recovery, ordering",
        "tests/test_simulation.py": "Successful and rejected transitions, blocked actions, snapshots",
        "tests/test_scenarios.py": "Six end-to-end scenarios, serialisation, no preloaded diagnoses",
        "tests/test_coverage.py": "60 rules, 12 per module, ≥50 conditions, every rule reachable",
    }
    rows = [
        [f"`{filename}`", count, purposes.get(filename, "—")]
        for filename, count in sorted(counts.items())
    ]
    rows.append(["**Total**", sum(counts.values()), ""])
    return table(["Test file", "Tests", "What it verifies"], rows, ["---", "---:", "---"])


def run_pytest() -> tuple[str, int]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (result.stdout + result.stderr).replace("\r", "")
    lines = [line for line in output.splitlines() if line.strip()]
    tail = lines[-3:] if len(lines) >= 3 else lines
    passed = 0
    for line in lines:
        match = re.search(r"(\d+) passed", line)
        if match:
            passed = int(match.group(1))
    block = "$ python -m pytest -q\n" + "\n".join(tail)
    return block, passed


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------
FIGURES = [
    ("01_overview", "Security Overview after four investigations. The metrics, severity chart and knowledge-base summary are computed from stored investigation records and the live rule objects."),
    ("02_knowledge_base", "Knowledge Base. The sidebar and the metric cards report 60 rules, 85 logical conditions, 80 distinct fact fields and 5 modules; the green banner confirms structural validation."),
    ("03_rule_auth04", "AUTH-04 expanded. The three declarative conditions, the IF/THEN statement, Critical severity and the NIST SP 800-61 Rev. 3 source are all inspectable."),
    ("16_pol12_rule", "POL-12, the cross-module rule. Its second condition is `possible_account_compromise`, which is the conclusion of AUTH-04."),
    ("04_condition_inventory", "Condition inventory (excerpt). The table is generated from the rule objects and reports how many conditions and distinct rules reference each fact field."),
    ("05_scenario_scn001_result", "SCN-001 after loading. The scenario supplies only observations and entity IDs; running it produces 4 activations and 4 findings."),
    ("06_trace_activations", "Inference Trace. AUTH-01 → AUTH-02 → AUTH-03 → AUTH-04 is the real firing order, and the reasoning log records observations, start, activations and finish."),
    ("07_justification_auth04", "Justification for AUTH-04. Every condition is shown with its expected value, observed value and Satisfied status, followed by the conclusion and source."),
    ("08_working_memory", "Working memory. Observations are separated from derived conclusions, and every derived fact records the rule that produced it and the facts that supported it."),
    ("09_response_proposed", "Response Center. Four findings are diagnosed, but only the actionable AUTH-04 finding creates a response: disable `account:USER-101`, executable Yes."),
    ("10_response_executed", "Execution result. The success message and the simulation snapshot prove the state change: `status=Active → status=Disabled` for `USER-101`."),
    ("11_scn005_result", "SCN-005. The privilege scenario derives 16 findings and 16 activations, including the cross-module coordinated compromise."),
    ("13b_history_detail", "History detail for SCN-005. The findings table includes Coordinated privilege compromise; the activation table mixes POL and AUTH rules, proving cross-module chaining."),
    ("13_history", "Investigation History. Each record stores its scenario, finding count, critical count and executed-action count; the JSON export contains the full records."),
    ("12_new_investigation", "New Investigation. Boolean observations use three explicit states — Unknown, True and False — while entity identifiers are supplied separately."),
    ("15_edge_no_finding", "Edge case: threshold not met. Three failed logins with Unknown Booleans produce 0 activations, 0 findings and 0 actions."),
    ("14_edge_invalid_target", "Edge case: invalid target. The full evidence still derives 4 findings and 1 proposed action, but the target is `USER-999`."),
    ("14b_blocked_actions", "The decision engine blocks the action because `USER-999` does not exist in the simulated inventory. `Executable: No`, a reason is shown, and no Execute button appears."),
]


def figure_html() -> str:
    parts = []
    for index, (name, caption) in enumerate(FIGURES, start=1):
        path = SHOTS / f"{name}.png"
        if not path.exists():
            raise FileNotFoundError(f"missing screenshot: {path}")
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        caption_html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html.escape(caption))
        parts.append(
            f'<figure id="fig{index}">'
            f'<img src="data:image/png;base64,{encoded}" alt="{html.escape(caption)}">'
            f'<figcaption><span class="fig-num">Figure {index}.</span> {caption_html}</figcaption>'
            "</figure>"
        )
    return "\n".join(parts)


def keep_small_tables(body_html: str) -> str:
    """Prevent small tables from splitting and keep ID columns on one line."""

    def replace(match: re.Match[str]) -> str:
        block = match.group(0)
        classes = []
        if block.count("<tr") <= 9:
            classes.append("keep")
        heads = [
            re.sub(r"<[^>]+>", "", cell).strip()
            for cell in re.findall(r"<th[^>]*>(.*?)</th>", block, re.S)
        ]
        if heads[:1] == ["ID"]:
            classes.append("idcol")
        if heads[:2] == ["ID", "Rule"]:
            classes.append("catalogue")
        if not classes:
            return block
        return block.replace("<table>", f'<table class="{" ".join(classes)}">', 1)

    body_html = re.sub(r"<table>.*?</table>", replace, body_html, flags=re.S)

    def soft_breaks(match: re.Match[str]) -> str:
        block = match.group(0)
        return re.sub(
            r"<code>([^<]*)</code>",
            lambda cell: "<code>" + cell.group(1).replace("_", "_<wbr>") + "</code>",
            block,
        )

    body_html = re.sub(r"<table[^>]*>.*?</table>", soft_breaks, body_html, flags=re.S)

    def long_pre(match: re.Match[str]) -> str:
        block = match.group(0)
        if block.count("\n") >= 13:
            return block.replace("<pre>", '<pre class="long">', 1)
        return block

    return re.sub(r"<pre>.*?</pre>", long_pre, body_html, flags=re.S)


# ---------------------------------------------------------------------------
# HTML shell
# ---------------------------------------------------------------------------
CSS = """
:root {
  --navy: #0f2a43;
  --navy-2: #163b5c;
  --teal: #0f766e;
  --teal-light: #0d9488;
  --ink: #24303f;
  --muted: #5a6b7f;
  --line: #d7e0ea;
  --panel: #f4f8fb;
}
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body {
  margin: 0;
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  font-size: 10.1pt;
  line-height: 1.55;
  color: var(--ink);
}
h1, h2, h3, h4 { color: var(--navy); line-height: 1.25; }
h2 {
  font-size: 19pt;
  margin: 22pt 0 10pt 0;
  padding-bottom: 5pt;
  border-bottom: 2.2pt solid var(--teal);
  break-before: auto;
  break-after: avoid;
}
.article > h2:first-child { margin-top: 0; }
h3 {
  font-size: 12.6pt;
  margin: 15pt 0 6pt 0;
  color: var(--teal);
  break-after: avoid;
}
h4 { font-size: 10.8pt; margin: 11pt 0 4pt 0; break-after: avoid; }
p { margin: 0 0 7pt 0; orphans: 2; widows: 2; }
strong { color: #12283d; }
a { color: var(--teal); text-decoration: none; }
ul, ol { margin: 0 0 8pt 0; padding-left: 17pt; }
li { margin: 0 0 3pt 0; }
table {
  width: 100%;
  border-collapse: collapse;
  margin: 7pt 0 11pt 0;
  font-size: 8.35pt;
  line-height: 1.34;
}
thead { display: table-header-group; }
th {
  background: var(--navy);
  color: #ffffff;
  text-align: left;
  font-weight: 600;
  padding: 4.2pt 4.5pt;
  border: 0.6pt solid var(--navy);
}
td {
  padding: 3.6pt 4.5pt;
  border: 0.6pt solid var(--line);
  vertical-align: top;
}
tbody tr:nth-child(even) td { background: #f6f9fc; }
tr { break-inside: avoid; }
code {
  font-family: Consolas, "Cascadia Mono", "Courier New", monospace;
  font-size: 8.7pt;
  background: #eef3f8;
  border: 0.5pt solid #dbe5ef;
  border-radius: 2pt;
  padding: 0.4pt 2.4pt;
  color: #123a56;
}
pre {
  background: #0e1e30;
  color: #e5edf6;
  border-radius: 4pt;
  padding: 8pt 10pt;
  margin: 7pt 0 11pt 0;
  font-size: 7.9pt;
  line-height: 1.38;
  white-space: pre-wrap;
  word-break: break-word;
  break-inside: avoid;
}
pre code { background: transparent; border: 0; color: inherit; padding: 0; font-size: inherit; }
pre.long { break-inside: auto; }
blockquote {
  margin: 8pt 0 10pt 0;
  padding: 6pt 10pt;
  background: #eef8f6;
  border-left: 3.5pt solid var(--teal);
  color: #173d3a;
}
hr { border: 0; border-top: 0.7pt solid var(--line); margin: 14pt 0; }
figure {
  margin: 6pt 0 8pt 0;
  padding: 4pt;
  border: 0.7pt solid var(--line);
  border-radius: 4pt;
  background: #ffffff;
  break-inside: avoid;
}
figure img { display: block; width: 78%; height: auto; margin: 0 auto; border-radius: 2pt; }
figcaption { font-size: 8pt; color: var(--muted); margin-top: 4pt; line-height: 1.35; }
.fig-num { color: var(--teal); font-weight: 700; }
table.keep { break-inside: avoid; }
table th, table td { overflow-wrap: break-word; }
table.idcol th:first-child, table.idcol td:first-child { white-space: nowrap; }
table.catalogue { table-layout: fixed; font-size: 8.1pt; }
table.catalogue td { padding: 3pt 3.5pt; }
table.catalogue code { font-size: 7.2pt; }
table.catalogue th:nth-child(1) { width: 8%; }
table.catalogue th:nth-child(2) { width: 13.5%; }
table.catalogue th:nth-child(3) { width: 22%; }
table.catalogue th:nth-child(4) { width: 22%; }
table.catalogue th:nth-child(5) { width: 9%; }
table.catalogue th:nth-child(6) { width: 14%; }
table.catalogue th:nth-child(7) { width: 11.5%; }
h2[id$="streamlit-interface-screenshots"],
h2#appendix-b-condition-inventory { break-before: page; }
.toc { break-after: page; }
.toc h2 { break-before: avoid; }
.toc-list {
  columns: 2;
  column-gap: 12mm;
  list-style: none;
  padding: 0;
  margin: 10pt 0 0 0;
  font-size: 9.6pt;
}
.toc-list li { margin: 0 0 5pt 0; break-inside: avoid; }
.toc-list a { color: var(--navy); }
.toc-list .toc-num { color: var(--teal); font-weight: 700; display: inline-block; min-width: 21pt; }
.notice {
  background: #fff7e8;
  border: 0.7pt solid #f0c987;
  border-left: 3.5pt solid #d97706;
  padding: 7pt 10pt;
  margin: 8pt 0 11pt 0;
  font-size: 9.2pt;
}
"""

COVER_CSS = """
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  background: #ffffff;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
.cover {
  height: 261mm;
  background: linear-gradient(150deg, #081626 0%, #0d2237 48%, #10344b 100%);
  color: #eaf2f8;
  padding: 20mm 17mm;
  border-radius: 5pt;
  position: relative;
  overflow: hidden;
}
.cover::after {
  content: "";
  position: absolute;
  right: -38mm; top: -38mm;
  width: 120mm; height: 120mm;
  border-radius: 50%;
  background: rgba(13, 148, 136, 0.16);
}
.cover::before {
  content: "";
  position: absolute;
  left: -30mm; bottom: -40mm;
  width: 110mm; height: 110mm;
  border-radius: 50%;
  background: rgba(56, 189, 248, 0.10);
}
.kicker {
  font-size: 9.5pt; letter-spacing: 2.4pt; text-transform: uppercase;
  color: #5eead4; font-weight: 600; margin-bottom: 14mm;
}
.mark {
  display: inline-block; width: 17mm; height: 17mm; line-height: 17mm;
  text-align: center; font-size: 20pt; font-weight: 800; color: #06202e;
  background: linear-gradient(135deg, #5eead4, #38bdf8);
  border-radius: 4mm; margin-bottom: 8mm;
}
h1 {
  font-size: 62pt; line-height: 0.95; margin: 0 0 5mm 0;
  letter-spacing: 2pt; color: #ffffff; font-weight: 800;
}
.subtitle {
  font-size: 17pt; line-height: 1.28; color: #cfe4f2; font-weight: 400;
  max-width: 145mm; margin-bottom: 11mm;
}
.doc-type {
  font-size: 12.5pt; color: #5eead4; font-weight: 600; letter-spacing: 1.1pt;
  text-transform: uppercase; margin-bottom: 8mm;
}
.desc {
  font-size: 10.4pt; line-height: 1.6; color: #a9c2d4; max-width: 132mm;
}
.stats {
  margin-top: 11mm; display: grid; grid-template-columns: 1fr 1fr; gap: 5mm;
  max-width: 116mm;
}
.stat {
  border: 0.7pt solid rgba(94, 234, 212, 0.42);
  background: rgba(8, 32, 48, 0.55);
  border-radius: 4pt; padding: 3.6mm 4.6mm;
}
.stat b { display: block; font-size: 18pt; color: #ffffff; line-height: 1.1; }
.stat span { font-size: 8.2pt; color: #8fb2c9; text-transform: uppercase; letter-spacing: 1pt; }
.meta {
  position: absolute; left: 17mm; right: 17mm; bottom: 15mm;
  border-top: 0.7pt solid rgba(148, 184, 206, 0.35);
  padding-top: 5mm; display: flex; justify-content: space-between;
  font-size: 8.5pt; color: #8fb2c9;
}
"""


def build_cover() -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><style>{COVER_CSS}</style></head>
<body>
<div class="cover">
  <div class="kicker">Expert Systems · Cybersecurity · Streamlit</div>
  <div class="mark">C</div>
  <h1>CIARES</h1>
  <div class="subtitle">Cybersecurity Incident Analysis and Response Expert System</div>
  <div class="doc-type">Technical and Code Explanation</div>
  <div class="desc">
    A rule-based Expert System that investigates security incidents, derives findings,
    recommends a response, executes it against a simulated environment, and explains
    every conclusion. This document explains the architecture, the knowledge base,
    the inference and decision engines, the simulation layer, the interface and the
    verification suite.
  </div>
  <div class="stats">
    <div class="stat"><b>{len(ALL_RULES)}</b><span>IF–THEN rules</span></div>
    <div class="stat"><b>{REPORT.condition_count}</b><span>Logical conditions</span></div>
    <div class="stat"><b>{len(MODULES)}</b><span>Knowledge modules</span></div>
    <div class="stat"><b>{PASSED_COUNT}</b><span>Passing tests</span></div>
  </div>
  <div class="meta">
    <span>Version 1.0.0 · Python 3 · Streamlit</span>
    <span>{TODAY}</span>
  </div>
</div>
</body></html>
"""


def build_toc(body_html: str) -> str:
    headings = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body_html, re.S)
    items = []
    for anchor, raw in headings:
        text = html.unescape(re.sub(r"<[^>]+>", "", raw)).strip()
        match = re.match(r"^(\d+)\.\s*(.*)$", text)
        if match:
            items.append(
                f'<li><a href="#{anchor}"><span class="toc-num">{match.group(1)}.</span>'
                f"{html.escape(match.group(2))}</a></li>"
            )
        elif text.startswith("Appendix"):
            letter = text.split()[1]
            rest = text.split("—", 1)[-1].strip()
            items.append(
                f'<li><a href="#{anchor}"><span class="toc-num">{letter}</span>'
                f"{html.escape(rest)}</a></li>"
            )
        else:
            items.append(
                f'<li><a href="#{anchor}"><span class="toc-num">·</span>'
                f"{html.escape(text)}</a></li>"
            )
    return (
        '<nav class="toc"><h2 class="toc-heading">Contents</h2>'
        '<ol class="toc-list">'
        '<li><a href="#"><span class="toc-num">1.</span>Cover page</a></li>'
        + "".join(items) + "</ol></nav>"
    )


def build_document(body_html: str) -> str:
    toc = build_toc(body_html)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><style>{CSS}</style></head>
<body>
{toc}
<article class="article">
{body_html}
</article>
</body></html>
"""


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def render_markdown(template: str, mapping: dict[str, str]) -> str:
    text = template
    for key, value in mapping.items():
        text = text.replace("{{" + key + "}}", value)
    missing = sorted(set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", text)) - {"FIGURES"})
    if missing:
        raise ValueError(f"unresolved placeholders: {', '.join(missing)}")
    return markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "toc", "sane_lists", "md_in_html"],
        extension_configs={"toc": {"permalink": False}},
    )


def run_node(html_path: Path, pdf_path: Path, plain: bool = False) -> None:
    command = ["node", str(NODE), str(html_path), str(pdf_path)]
    if plain:
        command.append("plain")
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"PDF print failed:\n{result.stdout}\n{result.stderr}"
        )
    print(result.stdout.strip())


def merge_pdfs(cover_pdf: Path, body_pdf: Path, output: Path) -> None:
    writer = PdfWriter()
    for page in PdfReader(str(cover_pdf)).pages:
        writer.add_page(page)
    for page in PdfReader(str(body_pdf)).pages:
        writer.add_page(page)
    writer.add_metadata(
        {
            "/Title": (
                "CIARES - Cybersecurity Incident Analysis and Response Expert System: "
                "Technical and Code Explanation"
            ),
            "/Subject": "Rule-based Expert System: architecture, knowledge base and code",
            "/Author": "CIARES Project",
            "/Creator": "CIARES documentation build",
            "/Producer": "CIARES build_pdf.py + Chromium",
        }
    )
    with output.open("wb") as handle:
        writer.write(handle)


def main() -> None:
    global PASSED_COUNT

    print("Collecting project data ...")
    pytest_block, PASSED_COUNT = run_pytest()
    print(f"  pytest: {PASSED_COUNT} passed")

    mapping = {
        "RULE_COUNT": str(len(ALL_RULES)),
        "CONDITION_COUNT": str(REPORT.condition_count),
        "FACT_FIELD_COUNT": str(REPORT.distinct_condition_fields),
        "MODULE_COUNT": str(len(MODULES)),
        "ACTIONABLE_COUNT": str(sum(1 for rule in ALL_RULES if rule.is_actionable)),
        "ACTION_COUNT": str(len(ACTION_LIBRARY)),
        "TEST_COUNT": str(PASSED_COUNT),
        "MODULE_TABLE": build_module_table(),
        "SEVERITY_TABLE": build_severity_table(),
        "THRESHOLD_TABLE": build_threshold_table(),
        "ACTION_TABLE": build_action_table(),
        "SCENARIO_TABLE": build_scenario_table(),
        "SCENARIO_RESULT_TABLE": build_scenario_result_table(),
        "SCN001_TRACE": build_scn001_trace(),
        "SCN001_MEMORY": build_scn001_memory(),
        "SCN001_FINDINGS": build_scn001_findings(),
        "SCN001_JUSTIFICATION": build_scn001_justification(),
        "RULE_CATALOGUE": build_rule_catalogue(),
        "CONDITION_INVENTORY": build_condition_inventory(),
        "FILE_TREE": build_file_tree(),
        "FILE_TABLE": build_file_table(),
        "TEST_FILE_TABLE": build_test_table(),
        "PYTEST_OUTPUT": f"```text\n{pytest_block}\n```",
    }

    template = DOC.read_text(encoding="utf-8")
    body_html = render_markdown(template, mapping)
    body_html = re.sub(r"<p>\{\{FIGURES\}\}</p>", figure_html(), body_html)
    body_html = body_html.replace("{{FIGURES}}", figure_html())
    body_html = keep_small_tables(body_html)

    HTML_OUT.write_text(build_document(body_html), encoding="utf-8")
    print(f"  wrote {HTML_OUT.relative_to(ROOT)}")

    temp = Path(tempfile.mkdtemp(prefix="ciARES_pdf_", dir=tempfile.gettempdir()))
    cover_html = temp / "cover.html"
    body_file = temp / "body.html"
    cover_pdf = temp / "cover.pdf"
    body_pdf = temp / "body.pdf"
    cover_html.write_text(build_cover(), encoding="utf-8")
    body_file.write_text(build_document(body_html), encoding="utf-8")

    print("Printing cover ...")
    run_node(cover_html, cover_pdf, plain=True)
    print("Printing body ...")
    run_node(body_file, body_pdf)
    merge_pdfs(cover_pdf, body_pdf, PDF_OUT)

    size_mb = PDF_OUT.stat().st_size / 1024 / 1024
    pages = len(PdfReader(str(PDF_OUT)).pages)
    print(f"Wrote {PDF_OUT.name}: {pages} pages, {size_mb:.2f} MB")


PASSED_COUNT = 0

if __name__ == "__main__":
    main()
