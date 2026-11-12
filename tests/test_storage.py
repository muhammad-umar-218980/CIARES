"""SQLite persistence: round-trip, aggregates and admin events."""

from __future__ import annotations

import pytest

import storage.db as db
from engine.pipeline import run_investigation


@pytest.fixture(autouse=True)
def temporary_database(tmp_path):
    previous = db.DATABASE_PATH
    db.configure(tmp_path / "test.db")
    db.init_db()
    yield
    db.configure(previous)


def _investigation():
    return run_investigation(
        observations={
            "failed_login_attempts": 25,
            "successful_login_after_failures": True,
            "unusual_login_location": True,
            "login_to_disabled_account": False,
            "is_admin_account": True,
        },
        entities={"account_id": "USER-101", "session_id": "SESSION-204"},
        name="Storage round-trip",
    )


def test_save_and_list_one_record():
    investigation = _investigation()
    db.save_investigation(investigation)

    rows = db.list_investigations()
    assert len(rows) == 1
    assert rows[0]["id"] == investigation.id
    assert rows[0]["findings"] == 4
    assert rows[0]["source"] == "manual"
    assert rows[0]["activations"] == 4


def test_save_is_idempotent():
    investigation = _investigation()
    db.save_investigation(investigation)
    db.save_investigation(investigation)
    assert len(db.list_investigations()) == 1


def test_round_trip_preserves_reasoning():
    investigation = _investigation()
    db.save_investigation(investigation)

    loaded = db.load_investigation(investigation.id)
    assert loaded is not None
    assert loaded.name == investigation.name
    assert len(loaded.findings) == len(investigation.findings)
    assert [item.rule.id for item in loaded.activations] == [
        item.rule.id for item in investigation.activations
    ]
    assert loaded.activations[0].evaluations[0].status in {"Satisfied", "Not satisfied"}
    assert loaded.actions[0].action == investigation.actions[0].action
    assert loaded.severity_counts == investigation.severity_counts


def test_record_contains_derived_provenance():
    investigation = _investigation()
    db.save_investigation(investigation)

    record = db.load_record(investigation.id)
    assert record is not None
    derived = {item["key"]: item for item in record["derived"]}
    assert "possible_account_compromise" in derived
    assert derived["possible_account_compromise"]["rule_id"] == "AUTH-04"


def test_stats_aggregate_across_records():
    db.save_investigation(_investigation())
    db.save_investigation(_investigation())

    summary = db.stats()
    assert summary["investigations"] == 2
    assert summary["findings"] == 8
    assert summary["critical"] >= 2
    assert sum(summary["by_module"].values()) == 8


def test_clear_removes_every_record():
    db.save_investigation(_investigation())
    db.clear_investigations()
    assert db.list_investigations() == []


def test_admin_events_are_logged_newest_first():
    db.log_admin_event("login_ok", "admin@ciares.local")
    db.log_admin_event("logout", "admin@ciares.local")

    events = db.recent_admin_events()
    assert [event["event"] for event in events] == ["logout", "login_ok"]


def test_unknown_record_returns_none():
    assert db.load_investigation("INV-DOES-NOT-EXIST") is None
    assert db.load_record("INV-DOES-NOT-EXIST") is None
