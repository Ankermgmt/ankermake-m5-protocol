"""Filament profile store backed by SQLite."""

import sqlite3
import threading
import logging

log = logging.getLogger(__name__)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS filaments (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    name                    TEXT NOT NULL,
    brand                   TEXT DEFAULT '',
    material                TEXT DEFAULT 'PLA',
    color                   TEXT DEFAULT '#FFFFFF',
    nozzle_temp_other_layer INTEGER DEFAULT 220,
    nozzle_temp_first_layer INTEGER DEFAULT 225,
    bed_temp_other_layer    INTEGER DEFAULT 60,
    bed_temp_first_layer    INTEGER DEFAULT 65,
    flow_rate               REAL DEFAULT 1.0,
    filament_diameter       REAL DEFAULT 1.75,
    pressure_advance        REAL DEFAULT 0.0,
    max_volumetric_speed    REAL DEFAULT 15.0,
    travel_speed            INTEGER DEFAULT 120,
    perimeter_speed         INTEGER DEFAULT 60,
    infill_speed            INTEGER DEFAULT 80,
    cooling_enabled         INTEGER DEFAULT 1,
    cooling_min_fan_speed   INTEGER DEFAULT 0,
    cooling_max_fan_speed   INTEGER DEFAULT 100,
    seam_position           TEXT DEFAULT 'aligned',
    seam_gap                REAL DEFAULT 0.0,
    scarf_enabled           INTEGER DEFAULT 0,
    scarf_conditional       INTEGER DEFAULT 0,
    scarf_angle_threshold   INTEGER DEFAULT 155,
    scarf_length            REAL DEFAULT 20.0,
    scarf_steps             INTEGER DEFAULT 10,
    scarf_speed             INTEGER DEFAULT 100,
    retract_length          REAL DEFAULT 0.8,
    retract_speed           INTEGER DEFAULT 45,
    retract_lift_z          REAL DEFAULT 0.0,
    wipe_enabled            INTEGER DEFAULT 0,
    wipe_distance           REAL DEFAULT 1.5,
    wipe_speed              INTEGER DEFAULT 40,
    wipe_retract_before     INTEGER DEFAULT 0,
    notes                   TEXT DEFAULT '',
    created_at              TEXT DEFAULT (datetime('now'))
);
"""

# New columns added after initial release — used for ALTER TABLE migration.
_MIGRATION_COLUMNS = [
    ("nozzle_temp_first_layer", "INTEGER DEFAULT 225"),
    ("bed_temp_other_layer",    "INTEGER DEFAULT 60"),
    ("bed_temp_first_layer",    "INTEGER DEFAULT 65"),
    ("flow_rate",               "REAL DEFAULT 1.0"),
    ("cooling_min_fan_speed",   "INTEGER DEFAULT 0"),
    ("cooling_max_fan_speed",   "INTEGER DEFAULT 100"),
    ("seam_position",           "TEXT DEFAULT 'aligned'"),
    ("seam_gap",                "REAL DEFAULT 0.0"),
    ("scarf_enabled",           "INTEGER DEFAULT 0"),
    ("scarf_conditional",       "INTEGER DEFAULT 0"),
    ("scarf_angle_threshold",   "INTEGER DEFAULT 155"),
    ("scarf_length",            "REAL DEFAULT 20.0"),
    ("scarf_steps",             "INTEGER DEFAULT 10"),
    ("scarf_speed",             "INTEGER DEFAULT 100"),
    ("retract_length",          "REAL DEFAULT 0.8"),
    ("retract_speed",           "INTEGER DEFAULT 45"),
    ("retract_lift_z",          "REAL DEFAULT 0.0"),
    ("wipe_enabled",            "INTEGER DEFAULT 0"),
    ("wipe_distance",           "REAL DEFAULT 1.5"),
    ("wipe_speed",              "INTEGER DEFAULT 40"),
    ("wipe_retract_before",     "INTEGER DEFAULT 0"),
]

_DEFAULTS = [
    {
        "name": "Generic PLA",
        "brand": "Generic",
        "material": "PLA",
        "color": "#FFFFFF",
        "nozzle_temp_other_layer": 220,
        "nozzle_temp_first_layer": 225,
        "bed_temp_other_layer": 60,
        "bed_temp_first_layer": 65,
        "flow_rate": 1.0,
        "filament_diameter": 1.75,
        "pressure_advance": 0.04,
        "max_volumetric_speed": 15.0,
        "travel_speed": 150,
        "perimeter_speed": 60,
        "infill_speed": 80,
        "cooling_enabled": 1,
        "cooling_min_fan_speed": 20,
        "cooling_max_fan_speed": 100,
        "seam_position": "aligned",
        "seam_gap": 0.0,
        "scarf_enabled": 0,
        "scarf_conditional": 0,
        "scarf_angle_threshold": 155,
        "scarf_length": 20.0,
        "scarf_steps": 10,
        "scarf_speed": 100,
        "retract_length": 0.6,
        "retract_speed": 45,
        "retract_lift_z": 0.0,
        "wipe_enabled": 0,
        "wipe_distance": 1.5,
        "wipe_speed": 40,
        "wipe_retract_before": 0,
        "notes": "",
    },
    {
        "name": "Generic PETG",
        "brand": "Generic",
        "material": "PETG",
        "color": "#FFFFFF",
        "nozzle_temp_other_layer": 240,
        "nozzle_temp_first_layer": 245,
        "bed_temp_other_layer": 75,
        "bed_temp_first_layer": 80,
        "flow_rate": 1.0,
        "filament_diameter": 1.75,
        "pressure_advance": 0.07,
        "max_volumetric_speed": 10.0,
        "travel_speed": 130,
        "perimeter_speed": 50,
        "infill_speed": 70,
        "cooling_enabled": 1,
        "cooling_min_fan_speed": 30,
        "cooling_max_fan_speed": 80,
        "seam_position": "aligned",
        "seam_gap": 0.0,
        "scarf_enabled": 0,
        "scarf_conditional": 0,
        "scarf_angle_threshold": 155,
        "scarf_length": 20.0,
        "scarf_steps": 10,
        "scarf_speed": 100,
        "retract_length": 0.8,
        "retract_speed": 45,
        "retract_lift_z": 0.2,
        "wipe_enabled": 0,
        "wipe_distance": 1.5,
        "wipe_speed": 40,
        "wipe_retract_before": 0,
        "notes": "",
    },
    {
        "name": "Generic ABS",
        "brand": "Generic",
        "material": "ABS",
        "color": "#FFFFFF",
        "nozzle_temp_other_layer": 245,
        "nozzle_temp_first_layer": 250,
        "bed_temp_other_layer": 90,
        "bed_temp_first_layer": 95,
        "flow_rate": 1.0,
        "filament_diameter": 1.75,
        "pressure_advance": 0.05,
        "max_volumetric_speed": 12.0,
        "travel_speed": 150,
        "perimeter_speed": 60,
        "infill_speed": 80,
        "cooling_enabled": 0,
        "cooling_min_fan_speed": 0,
        "cooling_max_fan_speed": 15,
        "seam_position": "aligned",
        "seam_gap": 0.0,
        "scarf_enabled": 0,
        "scarf_conditional": 0,
        "scarf_angle_threshold": 155,
        "scarf_length": 20.0,
        "scarf_steps": 10,
        "scarf_speed": 100,
        "retract_length": 0.8,
        "retract_speed": 45,
        "retract_lift_z": 0.2,
        "wipe_enabled": 0,
        "wipe_distance": 1.5,
        "wipe_speed": 40,
        "wipe_retract_before": 0,
        "notes": "",
    },
    {
        "name": "Generic TPU",
        "brand": "Generic",
        "material": "TPU",
        "color": "#FFFFFF",
        "nozzle_temp_other_layer": 230,
        "nozzle_temp_first_layer": 235,
        "bed_temp_other_layer": 40,
        "bed_temp_first_layer": 45,
        "flow_rate": 1.0,
        "filament_diameter": 1.75,
        "pressure_advance": 0.1,
        "max_volumetric_speed": 5.0,
        "travel_speed": 100,
        "perimeter_speed": 30,
        "infill_speed": 40,
        "cooling_enabled": 1,
        "cooling_min_fan_speed": 30,
        "cooling_max_fan_speed": 60,
        "seam_position": "aligned",
        "seam_gap": 0.0,
        "scarf_enabled": 0,
        "scarf_conditional": 0,
        "scarf_angle_threshold": 155,
        "scarf_length": 20.0,
        "scarf_steps": 10,
        "scarf_speed": 100,
        "retract_length": 2.0,
        "retract_speed": 25,
        "retract_lift_z": 0.2,
        "wipe_enabled": 0,
        "wipe_distance": 1.5,
        "wipe_speed": 40,
        "wipe_retract_before": 0,
        "notes": "",
    },
]

_FIELDS = [
    "name", "brand", "material", "color",
    "nozzle_temp_other_layer", "nozzle_temp_first_layer",
    "bed_temp_other_layer", "bed_temp_first_layer",
    "flow_rate", "filament_diameter",
    "pressure_advance", "max_volumetric_speed",
    "travel_speed", "perimeter_speed", "infill_speed",
    "cooling_enabled", "cooling_min_fan_speed", "cooling_max_fan_speed",
    "seam_position", "seam_gap",
    "scarf_enabled", "scarf_conditional", "scarf_angle_threshold",
    "scarf_length", "scarf_steps", "scarf_speed",
    "retract_length", "retract_speed", "retract_lift_z",
    "wipe_enabled", "wipe_distance", "wipe_speed", "wipe_retract_before",
    "notes",
]


class FilamentStore:
    """Thread-safe SQLite filament profile store."""

    def __init__(self, db_path):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._lock:
            with self._connect() as conn:
                conn.executescript(_SCHEMA)
                self._migrate(conn)
                count = conn.execute("SELECT COUNT(*) FROM filaments").fetchone()[0]
                if count == 0:
                    self._seed_defaults(conn)
                conn.commit()

    def _migrate(self, conn):
        """Apply incremental schema migrations for existing databases.

        Handles:
        - Rename nozzle_temp -> nozzle_temp_other_layer (SQLite 3.25+)
        - Rename bed_temp -> bed_temp_other_layer (SQLite 3.25+)
        - ADD COLUMN for each new column that may not exist yet
        """
        # Rename legacy columns if they exist (SQLite >= 3.25.0)
        _renames = [
            ("nozzle_temp", "nozzle_temp_other_layer"),
            ("bed_temp",    "bed_temp_other_layer"),
        ]
        for old_col, new_col in _renames:
            try:
                conn.execute(
                    f"ALTER TABLE filaments RENAME COLUMN {old_col} TO {new_col}"
                )
                log.info("Filament store: renamed column %s -> %s", old_col, new_col)
            except Exception:
                # Column doesn't exist (already renamed) or SQLite too old — skip
                pass

        # Add any missing new columns
        existing = {
            row[1]
            for row in conn.execute("PRAGMA table_info(filaments)").fetchall()
        }
        for col_name, col_def in _MIGRATION_COLUMNS:
            if col_name not in existing:
                try:
                    conn.execute(
                        f"ALTER TABLE filaments ADD COLUMN {col_name} {col_def}"
                    )
                    log.info("Filament store: added column %s", col_name)
                except Exception as exc:
                    log.warning("Filament store: could not add column %s: %s", col_name, exc)

    def _seed_defaults(self, conn):
        for profile in _DEFAULTS:
            cols = ", ".join(profile.keys())
            placeholders = ", ".join("?" for _ in profile)
            conn.execute(
                f"INSERT INTO filaments ({cols}) VALUES ({placeholders})",
                list(profile.values()),
            )
        log.info("Filament store: seeded %d default profiles", len(_DEFAULTS))

    def list_all(self):
        """Return all filament profiles as list of dicts, ordered by id."""
        with self._lock:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM filaments ORDER BY id ASC"
                ).fetchall()
                return [dict(r) for r in rows]

    def get(self, profile_id):
        """Return a single profile dict or None."""
        with self._lock:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM filaments WHERE id = ?", (profile_id,)
                ).fetchone()
                return dict(row) if row else None

    def create(self, data):
        """Insert a new profile. Returns the new profile dict."""
        safe = {k: data[k] for k in _FIELDS if k in data}
        if "name" not in safe or not safe["name"]:
            raise ValueError("name is required")
        cols = ", ".join(safe.keys())
        placeholders = ", ".join("?" for _ in safe)
        with self._lock:
            with self._connect() as conn:
                cur = conn.execute(
                    f"INSERT INTO filaments ({cols}) VALUES ({placeholders})",
                    list(safe.values()),
                )
                conn.commit()
                row = conn.execute(
                    "SELECT * FROM filaments WHERE id = ?", (cur.lastrowid,)
                ).fetchone()
                return dict(row)

    def update(self, profile_id, data):
        """Update an existing profile. Returns the updated profile dict or None."""
        safe = {k: data[k] for k in _FIELDS if k in data}
        if not safe:
            return self.get(profile_id)
        assignments = ", ".join(f"{k} = ?" for k in safe)
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    f"UPDATE filaments SET {assignments} WHERE id = ?",
                    list(safe.values()) + [profile_id],
                )
                conn.commit()
                row = conn.execute(
                    "SELECT * FROM filaments WHERE id = ?", (profile_id,)
                ).fetchone()
                return dict(row) if row else None

    def delete(self, profile_id):
        """Delete a profile. Returns True if deleted, False if not found."""
        with self._lock:
            with self._connect() as conn:
                cur = conn.execute(
                    "DELETE FROM filaments WHERE id = ?", (profile_id,)
                )
                conn.commit()
                return cur.rowcount > 0

    def duplicate(self, profile_id):
        """Duplicate a profile (copies all fields, appends ' (copy)' to name).

        Returns the new profile dict or None if source not found.
        """
        original = self.get(profile_id)
        if not original:
            return None
        copy = {k: original[k] for k in _FIELDS if k in original}
        copy["name"] = original["name"] + " (copy)"
        return self.create(copy)
