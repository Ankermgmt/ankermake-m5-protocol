"""Print history service backed by SQLite."""

import os
import sqlite3
import threading
import logging as log
from datetime import datetime, timedelta


_DEFAULT_RETENTION_DAYS = 90
_DEFAULT_MAX_ENTRIES = 500

_SCHEMA = """
CREATE TABLE IF NOT EXISTS print_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    filename    TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'started',
    started_at  TEXT NOT NULL,
    finished_at TEXT,
    duration_sec INTEGER,
    progress    INTEGER DEFAULT 0,
    failure_reason TEXT
);
"""


class PrintHistory:
    """Thread-safe SQLite print history store."""

    def __init__(self, db_path=None, retention_days=None, max_entries=None):
        self._db_path = db_path or os.path.expanduser("~/.config/ankerctl/history.db")
        self._retention_days = int(os.getenv("PRINT_HISTORY_RETENTION_DAYS", retention_days or _DEFAULT_RETENTION_DAYS))
        self._max_entries = int(os.getenv("PRINT_HISTORY_MAX_ENTRIES", max_entries or _DEFAULT_MAX_ENTRIES))
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    def _connect(self):
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _prune(self, conn):
        """Remove old entries beyond retention and max count."""
        if self._retention_days > 0:
            cutoff = (datetime.utcnow() - timedelta(days=self._retention_days)).isoformat()
            conn.execute("DELETE FROM print_history WHERE started_at < ?", (cutoff,))

        if self._max_entries > 0:
            conn.execute("""
                DELETE FROM print_history WHERE id NOT IN (
                    SELECT id FROM print_history ORDER BY id DESC LIMIT ?
                )
            """, (self._max_entries,))

    def record_start(self, filename):
        """Record a print start. Returns the row id.

        If an open 'started' entry for the same filename already exists (e.g. after a
        container restart mid-print), that entry is reused so the session continues
        cleanly.  Any orphaned entries for *different* filenames are closed first.
        """
        with self._lock:
            with self._connect() as conn:
                # Resume existing open entry for the same file (restart mid-print)
                if filename and filename != "unknown":
                    existing = conn.execute(
                        "SELECT id FROM print_history WHERE status='started' AND filename=?"
                        " ORDER BY id DESC LIMIT 1",
                        (filename,)
                    ).fetchone()
                    if existing:
                        log.info(f"History: resuming entry id={existing['id']} for {filename!r}")
                        conn.commit()
                        return existing["id"]

                # Close any orphaned entries that belong to a different (or unknown) job
                orphans = conn.execute(
                    "SELECT id, started_at FROM print_history WHERE status='started'"
                ).fetchall()
                if orphans:
                    now = datetime.utcnow()
                    for row in orphans:
                        started = datetime.fromisoformat(row["started_at"])
                        duration = int((now - started).total_seconds())
                        conn.execute(
                            "UPDATE print_history SET status='finished', finished_at=?,"
                            " duration_sec=? WHERE id=?",
                            (now.isoformat(), duration, row["id"]),
                        )
                    log.info(f"History: closed {len(orphans)} orphaned entries before new print")

                cur = conn.execute(
                    "INSERT INTO print_history (filename, status, started_at) VALUES (?, 'started', ?)",
                    (filename, datetime.utcnow().isoformat())
                )
                row_id = cur.lastrowid
                self._prune(conn)
                conn.commit()
                return row_id

    def record_finish(self, filename=None, progress=100):
        """Mark the most recent matching print as finished."""
        with self._lock:
            with self._connect() as conn:
                row = self._find_active(conn, filename)
                if not row:
                    log.debug("No active print to finish")
                    return
                now = datetime.utcnow()
                started = datetime.fromisoformat(row["started_at"])
                duration = int((now - started).total_seconds())
                conn.execute(
                    "UPDATE print_history SET status='finished', finished_at=?, duration_sec=?, progress=? WHERE id=?",
                    (now.isoformat(), duration, progress, row["id"])
                )
                conn.commit()

    def record_fail(self, filename=None, reason=None):
        """Mark the most recent matching print as failed."""
        with self._lock:
            with self._connect() as conn:
                row = self._find_active(conn, filename)
                if not row:
                    log.debug("No active print to fail")
                    return
                now = datetime.utcnow()
                started = datetime.fromisoformat(row["started_at"])
                duration = int((now - started).total_seconds())
                conn.execute(
                    "UPDATE print_history SET status='failed', finished_at=?, duration_sec=?, failure_reason=? WHERE id=?",
                    (now.isoformat(), duration, reason, row["id"])
                )
                conn.commit()

    def _find_active(self, conn, filename=None):
        """Find the most recent active print, optionally matching filename."""
        if filename:
            row = conn.execute(
                "SELECT * FROM print_history WHERE status='started' AND filename=? ORDER BY id DESC LIMIT 1",
                (filename,)
            ).fetchone()
            if row:
                return row
        return conn.execute(
            "SELECT * FROM print_history WHERE status='started' ORDER BY id DESC LIMIT 1"
        ).fetchone()

    def get_history(self, limit=50, offset=0):
        """Return recent print history as list of dicts."""
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM print_history ORDER BY id DESC LIMIT ? OFFSET ?",
                    (limit, offset)
                ).fetchall()
                return [dict(r) for r in rows]

    def get_count(self):
        """Return total number of entries."""
        with self._lock:
            with self._connect() as conn:
                return conn.execute("SELECT COUNT(*) FROM print_history").fetchone()[0]

    def clear(self):
        """Delete all history entries."""
        with self._lock:
            with self._connect() as conn:
                conn.execute("DELETE FROM print_history")
                conn.commit()
                log.info("Print history cleared")
