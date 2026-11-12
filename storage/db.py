"""
SQLite persistence for CIARES.

The Expert System keeps two records only:

* ``investigations`` - one row per investigation. The row carries the columns the
  admin dashboard aggregates over plus the full JSON payload needed to replay an
  investigation in the admin portal.
* ``admin_events``   - a small audit trail of admin sign-in activity.

Nothing in this module reasons about security incidents. It stores what the
engine produced so the admin portal can explain it later.

The database lives in ``data/ciares.db``. On Streamlit Community Cloud the
filesystem is ephemeral, so records survive while the container is awake and
reset after a redeploy or a long sleep. That limitation is stated to the user.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from config import DB_PATH
from engine.models import (
    ConditionEvaluation,
    Finding,
    Investigation,
    Phase,
    ResponseAction,
    RuleActivation,
    Severity,
)
from engine.report import threat_score
from knowledge_base.rule_registry import get_rule

# Tests point this at a temporary file; the app uses the configured path.
DATABASE_PATH: Path = DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS investigations (
    id                TEXT PRIMARY KEY,
    created_at        TEXT NOT NULL,
    name              TEXT NOT NULL,
    source            TEXT NOT NULL,
    scenario_id       TEXT,
    activation_count  INTEGER NOT NULL DEFAULT 0,
    finding_count     INTEGER NOT NULL DEFAULT 0,
    critical_count    INTEGER NOT NULL DEFAULT 0,
    high_count        INTEGER NOT NULL DEFAULT 0,
    medium_count      INTEGER NOT NULL DEFAULT 0,
    low_count         INTEGER NOT NULL DEFAULT 0,
    action_count      INTEGER NOT NULL DEFAULT 0,
    approved_count    INTEGER NOT NULL DEFAULT 0,
    score             INTEGER NOT NULL DEFAULT 0,
    terminated_reason TEXT,
    payload           TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_investigations_created
    ON investigations (created_at DESC);

CREATE TABLE IF NOT EXISTS admin_events (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    at     TEXT NOT NULL,
    event  TEXT NOT NULL,
    detail TEXT
);
"""


# ---------------------------------------------------------------------------
# Connection handling
# ---------------------------------------------------------------------------
def configure(path: Path | str | None) -> None:
    """Point the module at a different database file (used by tests)."""
    global DATABASE_PATH
    DATABASE_PATH = Path(path) if path is not None else DB_PATH


@contextmanager
def _connect(path: Path | str | None = None) -> Iterator[sqlite3.Connection]:
    target = Path(path) if path is not None else DATABASE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(target, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db(path: Path | str | None = None) -> None:
    """Create the tables if they do not exist. Safe to call on every rerun."""
    with _connect(path) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.executescript(SCHEMA)


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------
def _payload(investigation: Investigation) -> dict[str, Any]:
    """Build the JSON-safe record that can be rehydrated later."""
    memory = getattr(investigation, "memory", None)
    derived = []
    if memory is not None:
        derived = [
            {
                "key": fact.key,
                "value": fact.state,
                "rule_id": fact.rule_id,
                "supporting": [list(item) for item in fact.supporting],
            }
            for fact in memory.derived_facts()
        ]

    record = investigation.to_record()
    record["inference_cycles"] = investigation.inference_cycles
    record["derived"] = derived
    record["score"] = threat_score(investigation)
    return record


def _findings_from(record: dict[str, Any]) -> list[Finding]:
    return [
        Finding(
            key=item["key"],
            label=item["label"],
            severity=Severity(item["severity"]),
            module=item["module"],
            rule_ids=list(item.get("rule_ids", [])),
            supporting_facts=tuple(item.get("supporting_facts", ())),
            sequence=int(item.get("sequence", 0)),
            description=item.get("description", ""),
            recommended_action=item.get("recommended_action"),
            action_phase=Phase(item.get("action_phase", "Escalation")),
        )
        for item in record.get("findings", [])
    ]


def _activations_from(record: dict[str, Any]) -> list[RuleActivation]:
    activations: list[RuleActivation] = []
    for item in record.get("activations", []):
        rule = get_rule(item["rule_id"])
        evaluations = tuple(
            ConditionEvaluation(
                condition=condition,
                known=bool(evaluation["known"]),
                observed=evaluation["observed"],
                satisfied=evaluation["satisfied"],
                note=evaluation.get("note", ""),
            )
            for condition, evaluation in zip(rule.conditions, item.get("evaluations", []))
        )
        activations.append(
            RuleActivation(
                sequence=int(item["sequence"]),
                rule=rule,
                evaluations=evaluations,
                conclusion_key=item.get("conclusion_key", rule.conclusion_key),
                conclusion_label=item.get("conclusion_label", rule.conclusion_label),
                conclusion_value=item.get("conclusion_value", True),
                activation_key=item.get("activation_key", ""),
                inserted_new_fact=bool(item.get("inserted_new_fact", True)),
            )
        )
    return activations


def _actions_from(record: dict[str, Any]) -> list[ResponseAction]:
    return [
        ResponseAction(
            action=item["action"],
            label=item["label"],
            phase=Phase(item["phase"]),
            priority=int(item.get("priority", 99)),
            finding_key=item.get("finding_key", ""),
            finding_label=item.get("finding_label", ""),
            finding_severity=Severity(item.get("finding_severity", "Low")),
            reason=item.get("reason", ""),
            action_id=item.get("action_id", ""),
            approved=bool(item.get("approved", False)),
            deferred=bool(item.get("deferred", False)),
            defer_reason=item.get("defer_reason", ""),
        )
        for item in record.get("actions", [])
    ]


def rehydrate(record: dict[str, Any]) -> Investigation:
    """Rebuild an Investigation from a stored payload."""
    investigation = Investigation(
        id=record["id"],
        name=record.get("name", ""),
        started_at=record.get("started_at", ""),
        observations=dict(record.get("observations", {})),
        scenario_id=record.get("scenario_id"),
        approved_at=record.get("approved_at", ""),
        terminated_reason=record.get("terminated_reason", "completed"),
        inference_cycles=int(record.get("inference_cycles", 0)),
    )
    investigation.findings = _findings_from(record)
    investigation.activations = _activations_from(record)
    investigation.actions = _actions_from(record)
    investigation.trace = list(record.get("trace", []))
    return investigation


# ---------------------------------------------------------------------------
# Investigations
# ---------------------------------------------------------------------------
def save_investigation(
    investigation: Investigation, path: Path | str | None = None
) -> None:
    """Insert or replace one investigation (also used after approval)."""
    record = _payload(investigation)
    counts = investigation.severity_counts

    with _connect(path) as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO investigations (
                id, created_at, name, source, scenario_id,
                activation_count, finding_count,
                critical_count, high_count, medium_count, low_count,
                action_count, approved_count, score, terminated_reason, payload
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                investigation.id,
                investigation.started_at or datetime.now().isoformat(timespec="seconds"),
                investigation.name,
                "scenario" if investigation.scenario_id else "manual",
                investigation.scenario_id,
                len(investigation.activations),
                len(investigation.findings),
                counts["Critical"],
                counts["High"],
                counts["Medium"],
                counts["Low"],
                len(investigation.actions),
                len(investigation.approved_actions),
                threat_score(investigation),
                investigation.terminated_reason,
                json.dumps(record, indent=2),
            ),
        )


def investigation_exists(investigation_id: str, path: Path | str | None = None) -> bool:
    with _connect(path) as connection:
        row = connection.execute(
            "SELECT 1 FROM investigations WHERE id = ?", (investigation_id,)
        ).fetchone()
    return row is not None


def list_investigations(
    limit: int = 200,
    source: str | None = None,
    scenario_id: str | None = None,
    path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Summary rows for the audit table and the admin investigation selector."""
    clauses: list[str] = []
    params: list[Any] = []
    if source in {"manual", "scenario"}:
        clauses.append("source = ?")
        params.append(source)
    if scenario_id:
        clauses.append("scenario_id = ?")
        params.append(scenario_id)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"""
        SELECT id, created_at, name, source, scenario_id,
               activation_count, finding_count, critical_count, high_count,
               medium_count, low_count, action_count, approved_count, score,
               terminated_reason
        FROM investigations
        {where}
        ORDER BY created_at DESC
        LIMIT ?
    """
    params.append(int(limit))

    with _connect(path) as connection:
        rows = connection.execute(query, params).fetchall()
    return [
        {
            "id": row["id"],
            "created_at": row["created_at"],
            "name": row["name"],
            "source": row["source"],
            "scenario_id": row["scenario_id"],
            "activations": row["activation_count"],
            "findings": row["finding_count"],
            "Critical": row["critical_count"],
            "High": row["high_count"],
            "Medium": row["medium_count"],
            "Low": row["low_count"],
            "actions": row["action_count"],
            "approved": row["approved_count"],
            "score": row["score"],
            "terminated_reason": row["terminated_reason"],
        }
        for row in rows
    ]


def load_record(
    investigation_id: str, path: Path | str | None = None
) -> dict[str, Any] | None:
    """Return the raw stored payload (used for working-memory provenance)."""
    with _connect(path) as connection:
        row = connection.execute(
            "SELECT payload FROM investigations WHERE id = ?", (investigation_id,)
        ).fetchone()
    if row is None:
        return None
    return json.loads(row["payload"])


def load_investigation(
    investigation_id: str, path: Path | str | None = None
) -> Investigation | None:
    record = load_record(investigation_id, path)
    return None if record is None else rehydrate(record)


def stats(path: Path | str | None = None) -> dict[str, Any]:
    """Aggregates used by the admin dashboard."""
    with _connect(path) as connection:
        totals = connection.execute(
            """
            SELECT COUNT(*)             AS investigations,
                   COALESCE(SUM(finding_count), 0)  AS findings,
                   COALESCE(SUM(critical_count), 0) AS critical,
                   COALESCE(SUM(high_count), 0)     AS high,
                   COALESCE(SUM(medium_count), 0)   AS medium,
                   COALESCE(SUM(low_count), 0)      AS low,
                   COALESCE(SUM(action_count), 0)   AS actions,
                   COALESCE(SUM(approved_count), 0) AS approved,
                   COALESCE(AVG(score), 0)          AS average_score
            FROM investigations
            """
        ).fetchone()
        payloads = connection.execute("SELECT payload FROM investigations").fetchall()

    modules: dict[str, int] = {}
    for row in payloads:
        try:
            record = json.loads(row["payload"])
        except (TypeError, json.JSONDecodeError):
            continue
        for finding in record.get("findings", []):
            module = finding.get("module", "Unknown")
            modules[module] = modules.get(module, 0) + 1

    summary = {key: int(totals[key]) for key in ("investigations", "findings", "critical",
                                                 "high", "medium", "low", "actions", "approved")}
    summary["average_score"] = round(float(totals["average_score"] or 0), 1)
    summary["by_module"] = modules
    return summary


def clear_investigations(path: Path | str | None = None) -> None:
    with _connect(path) as connection:
        connection.execute("DELETE FROM investigations")


# ---------------------------------------------------------------------------
# Admin events
# ---------------------------------------------------------------------------
def log_admin_event(
    event: str, detail: str = "", path: Path | str | None = None
) -> None:
    with _connect(path) as connection:
        connection.execute(
            "INSERT INTO admin_events (at, event, detail) VALUES (?, ?, ?)",
            (datetime.now().isoformat(timespec="seconds"), event, detail),
        )


def recent_admin_events(
    limit: int = 10, path: Path | str | None = None
) -> list[dict[str, Any]]:
    with _connect(path) as connection:
        rows = connection.execute(
            "SELECT at, event, detail FROM admin_events ORDER BY id DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
    return [
        {"at": row["at"], "event": row["event"], "detail": row["detail"] or ""}
        for row in rows
    ]
