"""Print history service backed by SQLite."""

import os
import sqlite3
import threading
import logging
from datetime import datetime, timedelta, timezone

log = logging.getLogger("history")



_DEFAULT_RETENTION_DAYS = 90
_DEFAULT_MAX_ENTRIES = 500

_PLACEHOLDER_NAMES = frozenset({"unknown", "unknown.gcode", ""})

_SCHEMA = """
CREATE TABLE IF NOT EXISTS print_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    filename    TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'started',
    started_at  TEXT NOT NULL,
    finished_at TEXT,
    duration_sec INTEGER,
    progress    INTEGER DEFAULT 0,
    failure_reason TEXT,
    task_id     TEXT
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
            self._migrate_schema(conn)

    def _migrate_schema(self, conn):
        """Ensure schema is up to date."""
        try:
            # Check if task_id column exists
            cursor = conn.execute("PRAGMA table_info(print_history)")
            columns = [row[1] for row in cursor.fetchall()]
            if "task_id" not in columns:
                log.info("History: migrating schema, adding task_id column")
                conn.execute("ALTER TABLE print_history ADD COLUMN task_id TEXT")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_task_id ON print_history(task_id)")
        except Exception as e:
            log.warning(f"History: schema migration failed: {e}")


    def _connect(self):
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _prune(self, conn):
        """Remove old entries beyond retention and max count."""
        if self._retention_days > 0:
            cutoff = (datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=self._retention_days)).isoformat()
            conn.execute("DELETE FROM print_history WHERE started_at < ?", (cutoff,))

        if self._max_entries > 0:
            conn.execute("""
                DELETE FROM print_history WHERE id NOT IN (
                    SELECT id FROM print_history ORDER BY id DESC LIMIT ?
                )
            """, (self._max_entries,))

    def record_start(self, filename, task_id=None):
        """Record a print start. Returns the row id.

        If an open 'started' entry exists with the same task_id, it is resumed.
        Otherwise, any existing open entries are closed (orphaned) and a new one is created.

        Returns None immediately if *filename* is a placeholder (empty, 'unknown', etc.)
        to avoid polluting history with uninformative entries.
        """
        if not filename or filename.strip().lower() in _PLACEHOLDER_NAMES:
            log.debug(f"History: skipping placeholder filename {filename!r}")
            return None

        with self._lock:
            with self._connect() as conn:
                # 1. Resume existing open entry for the same task_id
                if task_id:
                    existing = conn.execute(
                        "SELECT id FROM print_history WHERE status='started' AND task_id=?",
                        (task_id,)
                    ).fetchone()
                    if existing:
                        log.info(f"History: resuming entry id={existing['id']} for task_id={task_id}")
                        conn.commit()
                        return existing["id"]

                # Fallback: Resume via filename if no task_id or legacy (only if same filename)
                # This is risky if job restarts, but we prefer task_id now.
                # If we have task_id, we trust it above filename.
                
                # 2. Close any *other* open entries (orphans)
                # If we reached here, we are starting a NEW print session.
                orp_sql = "SELECT id, started_at FROM print_history WHERE status='started'"
                orphans = conn.execute(orp_sql).fetchall()
                
                if orphans:
                    now = datetime.now(timezone.utc).replace(tzinfo=None)
                    for row in orphans:
                        # Optional: If we match via filename here? No, let's strictly rely on task_id for resume if possible.
                        # If task_id was NOT provided, maybe we fall back to filename matching?
                        # But caller (mqtt) usually provides task_id now.
                        
                        started = datetime.fromisoformat(row["started_at"])
                        duration = int((now - started).total_seconds())
                        conn.execute(
                            "UPDATE print_history SET status='interrupted', finished_at=?,"
                            " duration_sec=? WHERE id=?",
                            (now.isoformat(), duration, row["id"]),
                        )
                    log.info(f"History: marked {len(orphans)} orphaned entries as 'interrupted' before new print")

                # 3. Create new entry
                cur = conn.execute(
                    "INSERT INTO print_history (filename, status, started_at, task_id) VALUES (?, 'started', ?, ?)",
                    (filename, datetime.now(timezone.utc).replace(tzinfo=None).isoformat(), task_id)
                )
                row_id = cur.lastrowid
                self._prune(conn)
                conn.commit()
                return row_id


    def record_finish(self, filename=None, progress=100, task_id=None):
        """Mark the most recent matching print as finished."""
        with self._lock:
            with self._connect() as conn:
                row = self._find_active(conn, filename, task_id)
                if not row:
                    log.debug("No active print to finish")
                    return
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                started = datetime.fromisoformat(row["started_at"])
                duration = int((now - started).total_seconds())
                conn.execute(
                    "UPDATE print_history SET status='finished', finished_at=?, duration_sec=?, progress=? WHERE id=?",
                    (now.isoformat(), duration, progress, row["id"])
                )
                conn.commit()

    def record_fail(self, filename=None, reason=None, task_id=None):
        """Mark the most recent matching print as failed."""
        with self._lock:
            with self._connect() as conn:
                row = self._find_active(conn, filename, task_id)
                if not row:
                    log.debug("No active print to fail")
                    return
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                started = datetime.fromisoformat(row["started_at"])
                duration = int((now - started).total_seconds())
                conn.execute(
                    "UPDATE print_history SET status='failed', finished_at=?, duration_sec=?, failure_reason=? WHERE id=?",
                    (now.isoformat(), duration, reason, row["id"])
                )
                conn.commit()

    def _find_active(self, conn, filename=None, task_id=None):
        """Find the most recent active print, optionally matching task_id or filename."""
        # 1. Try task_id match (strongest)
        if task_id:
            row = conn.execute(
                "SELECT * FROM print_history WHERE status='started' AND task_id=?",
                (task_id,)
            ).fetchone()
            if row:
                return row

        # 2. Try filename match (legacy/fallback)
        if filename:
            row = conn.execute(
                "SELECT * FROM print_history WHERE status='started' AND filename=? ORDER BY id DESC LIMIT 1",
                (filename,)
            ).fetchone()
            if row:
                return row

        # 3. Fallback: Any active print (weakest)
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
