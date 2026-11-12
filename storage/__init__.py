"""Persistence layer: SQLite storage for investigations and admin events."""

from .db import (
    clear_investigations,
    configure,
    init_db,
    investigation_exists,
    list_investigations,
    load_investigation,
    load_record,
    log_admin_event,
    recent_admin_events,
    rehydrate,
    save_investigation,
    stats,
)

__all__ = [
    "clear_investigations",
    "configure",
    "init_db",
    "investigation_exists",
    "list_investigations",
    "load_investigation",
    "load_record",
    "log_admin_event",
    "recent_admin_events",
    "rehydrate",
    "save_investigation",
    "stats",
]
