# CLAUDE.md - AI Assistant Guide for AnkerMake M5 Protocol

## Project Overview

`ankerctl` is a CLI and web UI tool for monitoring, controlling, and interfacing with AnkerMake M5 3D printers. It provides an open-source alternative to the proprietary AnkerMake software, enabling local LAN control, slicer integration (PrusaSlicer, OrcaSlicer), and raw protocol access.

**License:** GPLv3
**Minimum Python Version:** 3.10
**Primary Entry Point:** `ankerctl.py`

## Architecture

The project follows a three-tier architecture:

1. **Protocol Layer** (`libflagship/`) - Binary protocol implementations
2. **API Layer** (`cli/` + `web/`) - User-facing interfaces
3. **UI Layer** (`static/`) - Web-based control panel

### Key Protocols

- **MQTT**: Encrypted (AES-256-CBC) topic-based messaging with Anker's cloud servers
- **PPPP**: Asymmetric UDP-based peer-to-peer protocol for LAN communication and file transfer
- **HTTP**: RESTful API for authentication and device management

## Directory Structure

```
ankermake-m5-protocol/
├── ankerctl.py              # Main CLI entry point (Click-based)
├── cli/                     # CLI command implementations
│   ├── config.py           # Configuration management
│   ├── mqtt.py             # MQTT CLI commands + mqtt_open/mqtt_gcode_dump helpers
│   ├── pppp.py             # PPPP CLI commands
│   ├── model.py            # Data models and default configs (Account, Printer, Config)
│   ├── logfmt.py           # Logging setup (setup_logging, named log files)
│   └── util.py             # CLI utilities (patch_gcode_time, extract_layer_count, etc.)
├── libflagship/            # Core protocol library
│   ├── mqtt.py             # [GENERATED] MQTT protocol implementation + MqttMsgType enum
│   ├── pppp.py             # [GENERATED] PPPP protocol implementation
│   ├── amtypes.py          # [GENERATED] Type definitions
│   ├── mqttapi.py          # MQTT API wrapper (AnkerMQTTBaseClient)
│   ├── ppppapi.py          # PPPP API wrapper (AnkerPPPPAsyncApi, FileUploadInfo)
│   ├── httpapi.py          # HTTP API client
│   ├── logincache.py       # Authentication & session management
│   └── notifications/      # Notification system (Apprise)
│       ├── apprise_client.py  # HTTP client for Apprise API
│       └── events.py          # Event constants (EVENT_PRINT_STARTED, etc.)
├── web/                    # Flask web server
│   ├── __init__.py         # Flask app, all routes, WebSocket handlers, debug API
│   ├── config.py           # Web configuration (config_import, config_login, config_show)
│   ├── notifications.py    # AppriseNotifier with live snapshot support
│   ├── lib/
│   │   └── service.py      # Thread-based service framework (Service, ServiceManager)
│   └── service/            # Backend services (all managed by ServiceManager)
│       ├── mqtt.py         # MqttQueue — MQTT state machine, print tracking,
│       │                   #             notifications, HA forwarding, timelapse hooks
│       ├── pppp.py         # PPPPService — LAN connection, XZYH/AABB framing
│       ├── video.py        # VideoQueue — camera streaming, light control, stall detect
│       ├── filetransfer.py # FileTransferService — web GCode upload pipeline
│       ├── history.py      # PrintHistory — SQLite-backed print log
│       ├── homeassistant.py# HomeAssistantService — HA MQTT Discovery + bidirectional light
│       ├── timelapse.py    # TimelapseService — ffmpeg snapshots + resume window
│       └── filament.py     # FilamentStore — SQLite-backed filament profile store
├── static/                 # Web UI assets
│   ├── ankersrv.js         # Main frontend JavaScript (Cash.js, Chart.js, AutoWebSocket)
│   ├── ankersrv.css        # Styling
│   ├── libflagship.js      # [GENERATED] Protocol JS
│   ├── base.html           # HTML shell / nav template
│   ├── index.html          # Main template (embeds tab HTML)
│   ├── tabs/               # UI tab HTML fragments
│   │   ├── home.html       # Live status, temperature chart, print controls
│   │   ├── setup.html      # Config, notifications, HA, bed level map, upload rate
│   │   ├── history.html    # Print history log
│   │   ├── filaments.html  # Filament profile manager
│   │   ├── timelapse.html  # Timelapse video gallery + player
│   │   └── debug.html      # Debug tab (dev mode only)
│   └── vendor/             # Third-party libraries (Bootstrap, JMuxer, Cash.js, Chart.js)
├── specification/          # Protocol specs for code generation
│   ├── mqtt.stf            # MQTT protocol specification
│   └── pppp.stf            # PPPP protocol specification
├── templates/              # Transwarp code generation templates
│   ├── python/             # Python templates
│   └── js/                 # JavaScript templates
├── examples/               # Example scripts for protocol testing
│   ├── mqtt-connect.py     # Test MQTT connectivity
│   ├── demo-pppp.py        # Test PPPP packet parsing
│   ├── web_login_test.py   # Test web authentication
│   └── probe_pppp_cmds.py  # Probe undocumented PPPP commands
└── documentation/          # Developer documentation
    └── MQTT_COMMANDS.md    # Full MQTT command type reference
```

## Build System and Code Generation

### Generated Files (DO NOT EDIT MANUALLY)

The following files are auto-generated by the `transwarp` code generator from `specification/*.stf` files:

- `libflagship/mqtt.py`
- `libflagship/pppp.py`
- `libflagship/amtypes.py`
- `static/libflagship.js`

**To modify these files, edit the templates in `templates/` or specs in `specification/` instead.**

### Makefile Commands

```bash
make update         # Regenerate protocol code from specification/
make diff           # Show codegen changes without writing files
make install-tools  # Install transwarp (git submodule + pip install)
make clean          # Remove __pycache__ and temp files
```

## Development Commands

### Running the Application

```bash
# Start web UI (default: http://localhost:4470)
./ankerctl.py webserver run

# Start web UI with custom host/port
./ankerctl.py webserver run --host 0.0.0.0 --port 8080

# Run via Docker
docker compose up
```

### Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# For development (includes additional tools)
pip install -r requirements-dev.txt

# Install code generation tools
make install-tools
```

**Note:** Python 3.10+ is required.

### CLI Quick Reference

```bash
# Configuration
./ankerctl.py config import [path/to/login.json]  # Import from file (auto-detects if omitted)
./ankerctl.py config login [COUNTRY]              # Login with email/password
./ankerctl.py config show                         # Display current config (tokens redacted)
./ankerctl.py config set-password [KEY]           # Set API key (random if omitted)
./ankerctl.py config remove-password              # Remove API key / disable auth
./ankerctl.py config decode [path/to/login.json]  # Decode login.json contents

# MQTT commands
./ankerctl.py mqtt monitor                    # Monitor real-time MQTT events
./ankerctl.py mqtt gcode                      # Interactive GCode prompt
./ankerctl.py mqtt rename-printer NAME        # Set printer nickname
./ankerctl.py mqtt send <CMD_TYPE> [key=val]  # Send raw MQTT command (expert use)
                                              # --force / -f  bypass safety guards
./ankerctl.py mqtt gcode-dump GCODE           # Send GCode, collect full ring-buffer output
                                              # --window SECS  collect window (default 3.0)
                                              # --drain N       send N M114 drain probes after main response

# PPPP commands
./ankerctl.py pppp lan-search                          # Find printers on local network
./ankerctl.py pppp print-file FILE                     # Upload and print a gcode file
                                                       # --no-act / -n  upload only, no print
                                                       # --upload-rate-mbps N  override rate
./ankerctl.py pppp capture-video -m 4mb output.h264   # Capture camera video

# HTTP utility commands
./ankerctl.py http calc-check-code DUID MAC  # Calculate check code (API v1)
./ankerctl.py http calc-sec-code DUID MAC    # Calculate security code (API v2)

# Webserver
./ankerctl.py webserver run                  # Start web UI

# Global options
./ankerctl.py -p INDEX ...          # Select printer by index (0-based)
./ankerctl.py -k ...                # Disable TLS verification (insecure)
./ankerctl.py -v/-q ...             # Increase/decrease verbosity
./ankerctl.py --pppp-dump FILE ...  # Enable PPPP packet capture
```

### Smoke Tests

```bash
./ankerctl.py mqtt monitor          # Quick MQTT connectivity check
./ankerctl.py pppp lan-search       # Quick PPPP/LAN check
```

## Coding Style and Conventions

### Python

- **Indentation:** 4 spaces
- **Naming:** `snake_case` for functions/variables, `CapWords` for classes
- **Imports:** Standard library first, then third-party, then local modules
- **Logging:** Use `cli.logfmt` for formatted output; use `log.info/warning/error/critical`
- **CLI:** Use Click decorators; follow existing patterns in `ankerctl.py`

### JavaScript

- Follow existing style in `static/ankersrv.js`
- Use Cash.js (lightweight jQuery alternative) for DOM manipulation
- Avoid introducing new frameworks

### General

- No enforced formatter/linter; keep diffs minimal and readable
- Follow existing module layouts and patterns
- Prefer editing existing files over creating new ones

## Testing Guidelines

**There is no automated test suite in this repository.**

### Manual Validation

1. Use CLI commands for smoke testing (`mqtt monitor`, `pppp lan-search`)
2. Test web UI at `http://localhost:4470`
3. Use scripts in `examples/` for protocol-specific testing

### Example Scripts

```bash
python examples/mqtt-connect.py      # Test MQTT connectivity
python examples/demo-pppp.py         # Test PPPP packet parsing
python examples/web_login_test.py    # Test web authentication
python examples/probe_pppp_cmds.py   # Probe undocumented PPPP commands
```

## Configuration

### Storage Location

- **Linux/macOS:** `~/.config/ankerctl/default.json`
- **Container:** `/home/ankerctl/.config/ankerctl/` (mounted volume)

### Sensitive Data

- `login.json` and configuration files contain sensitive tokens
- **Never commit** `login.json` or configuration files
- The `config show` command redacts sensitive values (user_id, auth_token)

### Environment Variables

```bash
# --- Server ---
PRINTER_INDEX          # Select printer (default: 0)
FLASK_HOST             # Web server host (default: 127.0.0.1)
FLASK_PORT             # Web server port (default: 4470)
FLASK_SECRET_KEY       # Session cookie secret (auto-generated if unset; set for persistence)
UPLOAD_MAX_MB          # Max file upload size in MB (default: 2048)

# --- Security ---
ANKERCTL_API_KEY       # API key for write-operation auth (unset = no auth)
                       # Takes precedence over key stored in config file

# --- Feature Flags ---
ANKERCTL_DEV_MODE=true   # Enable Debug tab and /api/debug/* endpoints (dev only)
ANKERCTL_LOG_DIR         # Directory for log files; enables file logging when set
                         # Default in CLI: /logs if /logs exists, else None
                         # Default in debug API: /logs

# --- Upload Rate ---
UPLOAD_RATE_MBPS       # Upload speed to printer in Mbit/s (choices: 5, 10, 25, 50, 100)
                       # Default: 10. Overrides the per-printer config file value.

# --- Apprise Notification Settings (all optional) ---
APPRISE_ENABLED=true                 # Enable/disable Apprise notifications
APPRISE_SERVER_URL=http://host:8000  # Apprise API server URL
APPRISE_KEY=ankerctl                 # Apprise notification key
APPRISE_TAG=critical                 # Optional tag filter

# Event toggles
APPRISE_EVENT_PRINT_STARTED=true
APPRISE_EVENT_PRINT_FINISHED=true
APPRISE_EVENT_PRINT_FAILED=true
APPRISE_EVENT_GCODE_UPLOADED=true
APPRISE_EVENT_PRINT_PROGRESS=true

# Progress settings
APPRISE_PROGRESS_INTERVAL=25         # Progress interval (%)
APPRISE_PROGRESS_INCLUDE_IMAGE=false # Attach snapshots to progress notifications
APPRISE_SNAPSHOT_QUALITY=hd          # 'sd' (848x480), 'hd' (1280x720), 'fhd' (1920x1080)
APPRISE_SNAPSHOT_FALLBACK=true       # Fallback to G-code preview image when no live snapshot
APPRISE_SNAPSHOT_LIGHT=false         # Turn printer light on for snapshot duration
APPRISE_PROGRESS_MAX=0               # Override progress scale divisor (0=auto-detect)

# --- Print History ---
PRINT_HISTORY_RETENTION_DAYS  # Days to keep history entries (default: 90)
PRINT_HISTORY_MAX_ENTRIES     # Max history entries (default: 500)

# --- Timelapse ---
TIMELAPSE_ENABLED=false        # Enable automatic timelapse capture (requires ffmpeg)
TIMELAPSE_INTERVAL_SEC=30      # Seconds between snapshot captures
TIMELAPSE_MAX_VIDEOS=10        # Max timelapse videos to keep (oldest pruned first)
TIMELAPSE_SAVE_PERSISTENT=true # Save assembled videos persistently
TIMELAPSE_CAPTURES_DIR=/captures  # Directory for timelapse video storage
TIMELAPSE_LIGHT                # Light control mode: 'snapshot' | 'session' | unset
                               # 'snapshot': light on, wait 1.5s, shoot, wait 1s, light off
                               # 'session': light on at capture start, off at finish

# --- Home Assistant MQTT Discovery ---
HA_MQTT_ENABLED=false          # Enable HA MQTT Discovery integration
HA_MQTT_HOST=localhost         # HA MQTT broker host
HA_MQTT_PORT=1883              # HA MQTT broker port
HA_MQTT_USER                   # MQTT broker username (optional)
HA_MQTT_PASSWORD               # MQTT broker password (optional)
HA_MQTT_DISCOVERY_PREFIX=homeassistant  # HA discovery prefix
HA_MQTT_TOPIC_PREFIX=ankerctl  # State/command topic prefix
```

## Web API Reference

All endpoints are served by `web/__init__.py`. Authentication is enforced by the
`_check_api_key()` before-request middleware when `ANKERCTL_API_KEY` is set.

### Authentication Rules

- **GET requests** are unauthenticated by default (read-only).
- **POST / DELETE requests** always require auth (session cookie, `X-Api-Key` header, or `?apikey=` param).
- **Protected GET paths** (listed in `_PROTECTED_GET_PATHS`) also require auth:
  `/api/ankerctl/server/reload`, `/api/debug/state`, `/api/debug/logs`, `/api/debug/services`.
- **All `/api/debug/*` paths** require auth (prefix match in middleware).
- **Setup paths** (`/api/ankerctl/config/upload`, `/api/ankerctl/config/login`) are exempt
  from auth when no printer is configured yet.

### General Endpoints

| Method | Path | Auth Required | Description |
|--------|------|--------------|-------------|
| `GET` | `/` | No | Render main UI page |
| `GET` | `/api/health` | No | Liveness probe — always returns `{"status": "ok"}` |
| `GET` | `/api/version` | No | OctoPrint-compatible version info |
| `GET` | `/video` | No | Raw H.264 video stream (use `?for_timelapse=1` for timelapse client) |

### Configuration Endpoints

| Method | Path | Auth Required | Description |
|--------|------|--------------|-------------|
| `POST` | `/api/ankerctl/config/upload` | Setup-exempt | Upload `login.json` file |
| `POST` | `/api/ankerctl/config/login` | Setup-exempt | Email/password login |
| `GET` | `/api/ankerctl/server/reload` | Yes | Reload config + restart all services |
| `POST` | `/api/ankerctl/config/upload-rate` | Yes | Set upload rate; form field `upload_rate_mbps` (choices: 5, 10, 25, 50, 100) |

### Printer Control Endpoints

| Method | Path | Auth Required | Description |
|--------|------|--------------|-------------|
| `POST` | `/api/printer/gcode` | Yes | Send GCode; JSON body `{"gcode": "G28"}`. Motion commands blocked while printing (returns 409). |
| `POST` | `/api/printer/control` | Yes | Print state control; JSON body `{"value": N}` — see Print Control Values below |
| `POST` | `/api/printer/autolevel` | Yes | Start auto-leveling (G29); blocked while printing |
| `GET` | `/api/printer/bed-leveling` | No | Read 7×7 bed level grid via M420 V (takes ~15s) |
| `GET` | `/api/printer/bed-leveling/last` | No | Return most recently saved bed level grid from log dir |
| `GET` | `/api/snapshot` | No | Capture a JPEG snapshot via ffmpeg from `/video`; returns file download |

**Print Control Values (empirically verified, ZZ_MQTT_CMD_PRINT_CONTROL):**

| Value | Action |
|-------|--------|
| `2` | Pause print |
| `3` | Resume paused print |
| `4` | Stop/cancel print |
| `0` | Restart print from beginning |

### Notification Endpoints

| Method | Path | Auth Required | Description |
|--------|------|--------------|-------------|
| `GET` | `/api/notifications/settings` | No | Return current Apprise config |
| `POST` | `/api/notifications/settings` | Yes | Update Apprise config; JSON body `{"apprise": {...}}` |
| `POST` | `/api/notifications/test` | Yes | Send test notification; optionally pass `{"apprise": {...}}` to override settings |

### Settings Endpoints

| Method | Path | Auth Required | Description |
|--------|------|--------------|-------------|
| `GET` | `/api/settings/timelapse` | No | Return current timelapse config |
| `POST` | `/api/settings/timelapse` | Yes | Update timelapse config; JSON body `{"timelapse": {...}}`; auto-reloads service |
| `GET` | `/api/settings/mqtt` | No | Return current Home Assistant MQTT config |
| `POST` | `/api/settings/mqtt` | Yes | Update HA MQTT config; JSON body `{"home_assistant": {...}}`; auto-reloads service |

### Print History Endpoints

| Method | Path | Auth Required | Description |
|--------|------|--------------|-------------|
| `GET` | `/api/history` | No | List history entries; query params: `limit=` (default 50), `offset=` (default 0). Returns `{"entries": [...], "total": N}` |
| `DELETE` | `/api/history` | Yes | Clear all history entries |

### Timelapse Endpoints

| Method | Path | Auth Required | Description |
|--------|------|--------------|-------------|
| `GET` | `/api/timelapses` | No | List videos; returns `{"videos": [{filename, size_bytes, created_at}], "enabled": bool}` |
| `GET` | `/api/timelapse/<filename>` | No | Download a video file (MP4) |
| `DELETE` | `/api/timelapse/<filename>` | Yes | Delete a video |

### Filament Profile Endpoints

| Method | Path | Auth Required | Description |
|--------|------|--------------|-------------|
| `GET` | `/api/filaments` | No | List all filament profiles |
| `POST` | `/api/filaments` | Yes | Create a profile; JSON body with profile fields |
| `PUT` | `/api/filaments/<id>` | Yes | Update a profile; JSON body with fields to change |
| `DELETE` | `/api/filaments/<id>` | Yes | Delete a profile |
| `POST` | `/api/filaments/<id>/apply` | Yes | Send M104/M140 to printer with profile temperatures |
| `POST` | `/api/filaments/<id>/duplicate` | Yes | Duplicate profile (appends " (copy)" to name) |

### Printer Selector Endpoints

| Method | Path | Auth Required | Description |
|--------|------|--------------|-------------|
| `GET` | `/api/printers` | No | List configured printers + `active_index` + `locked` flag |
| `POST` | `/api/printers/active` | Yes | Switch active printer; JSON body `{"index": N}`; blocked during print (409) or when `PRINTER_INDEX` env var is set (403) |

### Slicer Integration Endpoint

| Method | Path | Auth Required | Description |
|--------|------|--------------|-------------|
| `POST` | `/api/files/local` | Yes | OctoPrint-compatible file upload; form fields: `file` (GCode), `print` (bool) |

### WebSocket Endpoints

| Path | Direction | Description |
|------|-----------|-------------|
| `/ws/mqtt` | Server → Client | Raw MQTT message stream (JSON objects from MqttQueue) |
| `/ws/video` | Server → Client | Raw H.264 video frame stream |
| `/ws/pppp-state` | Server → Client | PPPP connection status (`{"status": "connected"}` / `{"status": "disconnected"}`) |
| `/ws/upload` | Server → Client | File upload progress events from FileTransferService |
| `/ws/ctrl` | Bidirectional | Light control (`{"light": bool}`), video quality (`{"video_profile": "sd"\|"hd"}`), video enable/disable (`{"video_enabled": bool}`) |

### Debug Endpoints (ANKERCTL_DEV_MODE=true only)

| Method | Path | Auth Required | Description |
|--------|------|--------------|-------------|
| `GET` | `/api/debug/state` | Yes | MqttQueue internal state JSON |
| `POST` | `/api/debug/config` | Yes | Set debug logging; JSON body `{"debug_logging": bool}` |
| `POST` | `/api/debug/simulate` | Yes | Fire simulated event; JSON body `{"type": "...", "payload": {...}}` |
| `GET` | `/api/debug/services` | Yes | Service health summary (state, refs, type) |
| `POST` | `/api/debug/services/<name>/restart` | Yes | Restart a named service asynchronously |
| `GET` | `/api/debug/logs` | Yes | List log files in `ANKERCTL_LOG_DIR` |
| `GET` | `/api/debug/logs/<filename>` | Yes | Tail log file; query param `?lines=N` (default 500) |
| `GET` | `/api/debug/bed-leveling` | Yes | Same as `/api/printer/bed-leveling` (debug alias) |

**Simulation event types** (`POST /api/debug/simulate`):

| type | payload fields | Description |
|------|---------------|-------------|
| `start` | `filename` | Simulate print start |
| `finish` | `filename` | Simulate print finish |
| `fail` | `filename` | Simulate print failure |
| `progress` | `progress` (0-100), `filename`, `elapsed`, `remaining` | Emit fake progress |
| `temperature` | `temp_type` (`nozzle`/`bed`), `current`, `target` (1/100 °C units) | Emit fake temperature |
| `speed` | `speed` (mm/s) | Emit fake speed |
| `layer` | `current_layer`, `total_layers` | Emit fake layer notification |

## Web Services Reference

All services are registered in `register_services()` in `web/__init__.py` and managed by
`ServiceManager` (in `web/lib/service.py`). Always access services via `app.svc.borrow("name")`.

### MqttQueue (`web/service/mqtt.py`)

Core service that drives the entire application. Maintains a persistent MQTT connection
to Anker's cloud servers and dispatches all printer events.

**Lifecycle:** `worker_init()` creates sub-services (PrintHistory, TimelapseService,
HomeAssistantService). `worker_start()` opens the MQTT connection. `worker_run()` polls
for messages every 100ms.

**Public methods:**

| Method | Description |
|--------|-------------|
| `get_state()` | Return structured state dict for debug inspection |
| `simulate_event(type, payload)` | Fire a synthetic event for testing |
| `set_debug_logging(enabled)` | Toggle verbose MQTT payload logging |
| `send_gcode(gcode)` | Send one or more GCode lines (100ms delay between lines) |
| `send_print_control(value)` | Send ZZ_MQTT_CMD_PRINT_CONTROL (2=pause, 3=resume, 4=stop) |
| `send_auto_leveling()` | Send ZZ_MQTT_CMD_AUTO_LEVELING |
| `set_gcode_layer_count(count)` | Store layer count from GCode header for UI display |
| `is_printing` | Property — True while a print is active |
| `history` | Property — `PrintHistory` instance |
| `timelapse` | Property — `TimelapseService` instance |
| `ha` | Property — `HomeAssistantService` instance |

**MQTT state machine (ct=1000):**

| value | Action |
|-------|--------|
| `1` | Print active — records start in history, starts timelapse, sends EVENT_PRINT_STARTED |
| `0` | Print ended — if stop was requested: record fail/cancelled; else: record finish, sends EVENT_PRINT_FINISHED |
| `2` | Print paused (no internal state change; ct=1008 value=2 triggers this) |
| `8` | Printer-side abort (touchscreen cancel) — record fail with reason "aborted" |

**Progress scale:** ct=1001 `progress` field is on a 0-1000 scale. `_normalize_progress()` converts to 0-100.

**Layer count:** ct=1052 (`ZZ_MQTT_CMD_MODEL_LAYER`) provides `real_print_layer` and `total_layer`. If `_gcode_layer_count` is set (from GCode header), `total_layer` is overridden before forwarding to WebSocket.

### PPPPService (`web/service/pppp.py`)

Manages the LAN (PPPP) connection to the printer. Reference-counted: started
when first `borrow()`ed, stopped when last reference is released.

**Key attributes:**

| Attribute | Description |
|-----------|-------------|
| `connected` | Property — True when PPPP API is in Connected state |
| `xzyh_handlers` | List of callbacks for XZYH frames (used by VideoQueue) |
| `api_command(commandType, **kwargs)` | Send a JSON command over PPPP channel 0 |

### VideoQueue (`web/service/video.py`)

Streams H.264 video frames from the printer camera over PPPP channel 1.

**Key attributes and methods:**

| Attribute / Method | Description |
|--------------------|-------------|
| `video_enabled` | Bool — whether streaming should be active |
| `last_frame_at` | `time.monotonic()` timestamp of last frame received; None if none yet |
| `saved_light_state` | Last-set light state (True/False/None). Not queried from hardware. |
| `saved_video_profile_id` | Last-set video profile ID (`"sd"`, `"hd"`) |
| `set_video_enabled(bool)` | Enable or disable video and start/stop service accordingly |
| `api_light_state(bool)` | Send LIGHT_STATE_SWITCH command over PPPP |
| `api_video_profile(id)` | Set video resolution profile (`"sd"`, `"hd"`) |
| `api_video_mode(mode)` | Set video mode by integer (0=SD, 1=HD) |

**Video profiles:**

| ID | Resolution | Notes |
|----|------------|-------|
| `"sd"` | 848×480 | Live streaming supported |
| `"hd"` | 1280×720 | Live streaming supported (default) |
| `"fhd"` | 1920×1080 | Snapshot-only, not live |

**Stall detection:** If active consumers exist but no frames arrive for 15 seconds, raises
`ServiceRestartSignal` to re-trigger `api_start_live()`.

### FileTransferService (`web/service/filetransfer.py`)

Handles the GCode file upload pipeline from web form submission to printer.
Calls `patch_gcode_time()` (time patching), `extract_layer_count()` (for layer display),
and `pppp_send_file()`. Progress events are streamed via `/ws/upload`.

### PrintHistory (`web/service/history.py`)

SQLite-backed print log. Not a `Service` subclass — instantiated directly by `MqttQueue`.

**Storage:** `~/.config/ankerctl/history.db`

**Schema:** `id, filename, status, started_at, finished_at, duration_sec, progress, failure_reason, task_id`

**Status values:** `started`, `finished`, `failed`, `interrupted`

**Public methods:**

| Method | Description |
|--------|-------------|
| `record_start(filename, task_id=None)` | Record print start; returns None for placeholder filenames |
| `record_finish(filename, progress, task_id)` | Mark print finished with duration |
| `record_fail(filename, reason, task_id)` | Mark print failed with reason |
| `get_history(limit, offset)` | Return entries as list of dicts |
| `get_count()` | Return total entry count |
| `clear()` | Delete all entries |

**Placeholder filenames ignored:** `"unknown"`, `"unknown.gcode"`, `""` — no entry is recorded.

### TimelapseService (`web/service/timelapse.py`)

Captures periodic JPEG snapshots during a print and assembles them into an MP4 video
with ffmpeg. Not a `Service` subclass — instantiated directly by `MqttQueue`.

**Key constants:**

| Constant | Value | Description |
|----------|-------|-------------|
| `_RESUME_WINDOW_SEC` | 3600 (60 min) | How long to wait before assembling after print finish |
| `_MAX_ORPHAN_AGE_SEC` | 86400 (24 h) | Max age of persisted frame dirs to resume on startup |
| `_SNAPSHOT_TIMEOUT` | 10s | ffmpeg timeout per frame |

**Resume window:** After `finish_capture(final=False)`, frames are held for 60 minutes. If
`start_capture()` is called with the same filename within that window, frames are reused
(filament-change resume). Pass `final=True` for definitive completion to skip the window.

**Persistent frames:** Frames are saved under `TIMELAPSE_CAPTURES_DIR/in_progress/<name>_<ts>/`
with a `.meta` sidecar. They survive container restarts and are picked up on startup.

**FPS formula:** `fps = max(1, min(30, ceil(frame_count / 30)))` — targets ~30-second videos.

**Public methods:**

| Method | Description |
|--------|-------------|
| `start_capture(filename)` | Begin capture; skips placeholder filenames and when disabled |
| `finish_capture(final=False)` | Stop capture; `final=True` assembles immediately, else enters resume window |
| `fail_capture()` | Stop and assemble partial timelapse (if >= 2 frames), cancel resume |
| `reload_config(config)` | Hot-reload config from ConfigManager |
| `list_videos()` | Return list of `{filename, size_bytes, created_at}` dicts |
| `get_video_path(filename)` | Return full path or None |
| `delete_video(filename)` | Delete a video; returns True/False |
| `enabled` | Property |

### HomeAssistantService (`web/service/homeassistant.py`)

Connects to an external MQTT broker (typically Home Assistant's) and publishes MQTT
Discovery payloads so the printer appears as a Home Assistant device.

**Published entities:** print_progress (sensor), print_status (sensor), nozzle_temp
(sensor), nozzle_temp_target (sensor), bed_temp (sensor), bed_temp_target (sensor),
print_speed (sensor), print_layer (sensor), print_filename (sensor), time_elapsed
(sensor), time_remaining (sensor), mqtt_connected (binary sensor), pppp_connected
(binary sensor), Printer Light (switch, bidirectional), Camera (MJPEG).

**Topics:**
- State: `<HA_MQTT_TOPIC_PREFIX>/<printer_sn>/state` (JSON, retained)
- Availability: `<HA_MQTT_TOPIC_PREFIX>/<printer_sn>/availability` (`online`/`offline`, retained)
- Light command: `<HA_MQTT_TOPIC_PREFIX>/<printer_sn>/light/set` (`ON`/`OFF`)

**Called from `MqttQueue._forward_to_ha()`** on each relevant MQTT message.

**Public methods:**

| Method | Description |
|--------|-------------|
| `start()` | Connect to broker and publish discovery |
| `stop()` | Disconnect and publish `offline` LWT |
| `update_state(**kwargs)` | Update cached state and publish to HA |
| `reload_config(config)` | Hot-reload config; reconnects if connection params changed |
| `enabled` | Property |

### FilamentStore (`web/service/filament.py`)

Thread-safe SQLite store for filament profiles. Not a `Service` subclass — instantiated
directly at startup in `webserver()` and attached to `app.filaments`.

**Storage:** `~/.config/ankerctl/filament.db`

**Pre-seeded defaults:** Generic PLA, Generic PETG, Generic ABS, Generic TPU

**Schema fields:** `id`, `name`, `brand`, `material`, `color`,
`nozzle_temp_other_layer`, `nozzle_temp_first_layer`,
`bed_temp_other_layer`, `bed_temp_first_layer`,
`flow_rate`, `filament_diameter`, `pressure_advance`, `max_volumetric_speed`,
`travel_speed`, `perimeter_speed`, `infill_speed`,
`cooling_enabled`, `cooling_min_fan_speed`, `cooling_max_fan_speed`,
`seam_position`, `seam_gap`,
`scarf_enabled`, `scarf_conditional`, `scarf_angle_threshold`, `scarf_length`, `scarf_steps`, `scarf_speed`,
`retract_length`, `retract_speed`, `retract_lift_z`,
`wipe_enabled`, `wipe_distance`, `wipe_speed`, `wipe_retract_before`,
`notes`, `created_at`

**Public methods:**

| Method | Description |
|--------|-------------|
| `list_all()` | Return all profiles as list of dicts, ordered by `id` |
| `get(profile_id)` | Return single profile dict or `None` |
| `create(data)` | Insert new profile; `name` is required; returns new profile dict |
| `update(profile_id, data)` | Update fields; returns updated profile dict or `None` |
| `delete(profile_id)` | Delete profile; returns `True` if deleted |
| `duplicate(profile_id)` | Copy profile with " (copy)" appended to name; returns new dict or `None` |

**Schema migrations:** New columns are added via `ALTER TABLE` on startup; column renames
(`nozzle_temp` → `nozzle_temp_other_layer`, `bed_temp` → `bed_temp_other_layer`) are
handled automatically for existing databases.

## Service Framework (`web/lib/service.py`)

### Service Base Class

`Service` extends `threading.Thread`. The background thread calls lifecycle methods:

| Method | When called |
|--------|------------|
| `worker_init()` | Once on thread start (before any state transitions) |
| `worker_start()` | Each time service transitions Stopped → Running |
| `worker_run(timeout)` | Repeatedly while Running |
| `worker_stop()` | Each time service transitions Running → Stopped |

**States:** `Starting` → `Running` → `Stopping` → `Stopped`

**Signals:** Raise `ServiceRestartSignal` from `worker_run()` to trigger a clean restart.

**Notify pattern:** `self.notify(data)` broadcasts `data` to all registered handlers
(appended to `self.handlers`). Used by `ServiceManager.stream()` to feed WebSocket queues.

### ServiceManager

Ref-counted lifecycle manager. The `svcs` dict holds service instances.

```python
# Safe service access (use this pattern everywhere in Flask routes)
with app.svc.borrow("mqttqueue") as mqtt:
    state = mqtt.get_state()
    mqtt.send_gcode("G28")

# Non-blocking read (does not wait for service to start)
pppp = app.svc.get("pppp", ready=False)
# ... use pppp ...
app.svc.put("pppp")

# Raw dict access without ref-counting (read-only, no lifecycle effect)
vq = app.svc.svcs.get("videoqueue")
```

**Warning:** Accessing a service attribute outside the `with borrow()` block is a
use-after-release bug — the service may have been stopped.

## Key Patterns and Idioms

### Click CLI Structure

```python
@main.group("groupname", help="Group description")
@pass_env
def groupname(env):
    env.load_config()

@groupname.command("subcommand")
@click.argument("arg", required=True)
@click.option("--flag", "-f", is_flag=True, help="Description")
@pass_env
def groupname_subcommand(env, arg, flag):
    """Docstring becomes help text."""
    # Implementation
```

### Environment Object Pattern

Commands use `@pass_env` decorator to access shared state:

```python
env.config        # Configuration manager
env.printer_index # Selected printer (0-based)
env.insecure      # TLS verification flag
env.pppp_dump     # PPPP debug log path
```

### MQTT Command Pattern

```python
client = cli.mqtt.mqtt_open(env.config, env.printer_index, env.insecure)
cmd = {
    "commandType": MqttMsgType.ZZ_MQTT_CMD_GCODE_COMMAND.value,
    "cmdData": "G28",
    "cmdLen": 3,
}
client.command(cmd)
response = client.await_response(MqttMsgType.ZZ_MQTT_CMD_GCODE_COMMAND)
```

### GCode Dump Pattern (for long responses)

```python
# Collects all response packets within a time window
msgs = cli.mqtt.mqtt_gcode_dump(client, "M420 V", collect_window=4.0)
combined = "\n".join(msg.get("resData", "") for msg in msgs)
```

### PPPP File Transfer Pattern

```python
api = cli.pppp.pppp_open(env.config, env.printer_index, dumpfile=env.pppp_dump)
fui = FileUploadInfo.from_data(data, filename, user_name="ankerctl", ...)
cli.pppp.pppp_send_file(api, fui, data, rate_limit_mbps=rate_limit_mbps)
api.aabb_request(b"", frametype=FileTransfer.END)  # Start print
api.stop()
```

### WebSocket Stream Pattern

```python
# Frontend: AutoWebSocket class with auto-reconnect in ankersrv.js
# Backend: service.notify() → ServiceManager.stream() → WebSocket
@sock.route("/ws/mqtt")
def mqtt_ws(sock):
    for data in app.svc.stream("mqttqueue"):
        sock.send(json.dumps(data))
```

`ServiceManager.stream()` uses a `Queue` tapped into `service.handlers`. It yields
items with a 1-second timeout to avoid blocking when the service stops.

### MQTT Message Flow (WebSocket to Frontend)

1. Printer sends message on MQTT topic `/phone/maker/{SN}/notice`.
2. `MqttQueue.worker_run()` → `client.fetch()` decrypts and returns payload dicts.
3. For ct=1052, `total_layer` is overridden with `_gcode_layer_count` if set.
4. `self.notify(obj)` sends raw dict to all handlers → WebSocket stream → frontend.
5. `self._forward_to_ha(obj)` processes same payload for Home Assistant updates.
6. `self._handle_notification(obj)` processes for Apprise, print history, and timelapse.

**Frontend** receives raw JSON and dispatches by `commandType`. No normalization of the
0-1000 `progress` scale is done server-side for WebSocket; the frontend handles display.

### Logging Convention

```python
import logging
log = logging.getLogger(__name__)  # preferred
# Named loggers with explicit names are also acceptable:
log = logging.getLogger("mqtt")    # produces mqtt.log when ANKERCTL_LOG_DIR is set
```

Named loggers that write to separate files: `mqtt`, `web`, `history`, `timelapse`, `homeassistant`.
Root logger output goes to `ankerctl.log` and stdout simultaneously.

`cli/logfmt.py` is the single source of truth for logging setup. Call `setup_logging(level, log_dir)`.

## Protocol Reference

### MQTT Topics

- **To Printer:** `/device/maker/{SN}/command`, `/device/maker/{SN}/query`
- **From Printer:** `/phone/maker/{SN}/notice`, `/phone/maker/{SN}/command/reply`, `/phone/maker/{SN}/query/reply`

### Common MQTT Commands

| Command | Hex | Decimal | Description |
|---------|-----|---------|-------------|
| `ZZ_MQTT_CMD_GCODE_COMMAND` | 0x0413 | 1043 | Send raw GCode (`cmdData`, `cmdLen` fields) |
| `ZZ_MQTT_CMD_NOZZLE_TEMP` | 0x03eb | 1003 | Set nozzle temp (value in 1/100 °C) |
| `ZZ_MQTT_CMD_HOTBED_TEMP` | 0x03ec | 1004 | Set bed temp (value in 1/100 °C) |
| `ZZ_MQTT_CMD_PRINT_CONTROL` | 0x03f0 | 1008 | 2=pause, 3=resume, 4=stop, 0=restart |
| `ZZ_MQTT_CMD_MOVE_ZERO` | 0x0402 | 1026 | Home axes (G28); ct=1026 in MQTT notifications |
| `ZZ_MQTT_CMD_AUTO_LEVELING` | 0x03ef | 1007 | Start auto-leveling (G29) |
| `ZZ_MQTT_CMD_APP_QUERY_STATUS` | 0x0403 | 1027 | Query current printer status (polled every 10s) |

### Common MQTT Notifications (Printer → ankerctl)

| commandType | Hex | Fields | Description |
|-------------|-----|--------|-------------|
| 1000 | 0x03e8 | `value` | State: 0=idle/done, 1=printing, 2=paused, 8=aborted |
| 1001 | 0x03e9 | `time`, `totalTime`, `progress` (0-1000), `name` | Print schedule/progress |
| 1003 | 0x03eb | `currentTemp`, `targetTemp` | Nozzle temp (1/100 °C) |
| 1004 | 0x03ec | `currentTemp`, `targetTemp` | Bed temp (1/100 °C) |
| 1006 | 0x03ee | `value` | Print speed (mm/s) |
| 1007 | 0x03ef | `value` | Auto-leveling probe progress; value = probe index (50 total: 1 center + 7×7) |
| 1044 | 0x0414 | `filePath` | GCode file path at print start; `basename(filePath)` = filename |
| 1052 | 0x041c | `real_print_layer`, `total_layer` | Layer progress |

**Note:** `progress` in ct=1001 is on a 0-1000 scale (not 0-100). Use `_normalize_progress()` in `MqttQueue` or divide by 10 for percentage.

See `documentation/MQTT_COMMANDS.md` for the full command type reference.

## Apprise Notification System

ankerctl includes a complete notification system via [Apprise API](https://github.com/caronc/apprise-api):

**Architecture:**
- **Client:** `libflagship/notifications/apprise_client.py` - HTTP client for Apprise API
- **Events:** `libflagship/notifications/events.py` - Event constants
- **Notifier:** `web/notifications.py` - `AppriseNotifier` class with live snapshot support
- **Hooks:** `web/service/mqtt.py` - Event hooks in `MqttQueue` for print events

**Supported Events:**
- Print started/finished/failed
- G-code file uploaded
- Print progress (configurable interval, default every 25%)

**Attachments:**
- Live camera snapshots (requires `ffmpeg` + active PPPP connection)
- Optional light control: `APPRISE_SNAPSHOT_LIGHT=true` turns on printer light for snapshot
- G-code preview images (fallback when live snapshot unavailable)

**Configuration:**
- Web UI: Setup → Notifications tab
- Environment variables (Docker deployments)
- Stored in `default.json` under `notifications.apprise`

## Print History

Automatic SQLite-backed print history log:

**Architecture:**
- **Service:** `web/service/history.py` - `PrintHistory` class
- **Storage:** `~/.config/ankerctl/history.db` (SQLite)
- **Integration:** `MqttQueue` records start/finish/fail events

**API endpoints:**
- `GET /api/history` - Return entries (supports `limit=` and `offset=` params)
- `DELETE /api/history` - Clear all history

**Configuration:** `PRINT_HISTORY_RETENTION_DAYS` (default: 90), `PRINT_HISTORY_MAX_ENTRIES` (default: 500)

## Timelapse

Automatic timelapse video capture during prints:

**Architecture:**
- **Service:** `web/service/timelapse.py` - `TimelapseService` class
- **UI Tab:** `static/tabs/timelapse.html`
- **Requires:** `ffmpeg` in `PATH`

**Behavior:**
- Captures periodic snapshots from the `/video` endpoint
- Assembles frames into MP4 video on print finish (or partial video on fail)
- Dynamic FPS to produce approximately 30-second videos
- Prunes oldest videos when `TIMELAPSE_MAX_VIDEOS` limit is reached
- Resume window: 60 minutes after `finish_capture()`, frames are preserved so the same print can resume (e.g. filament change)
- Frame directories (`TIMELAPSE_CAPTURES_DIR/in_progress/`) survive container restarts

**API endpoints:**
- `GET /api/timelapses` - List videos with metadata
- `GET /api/timelapse/<filename>` - Download a video
- `DELETE /api/timelapse/<filename>` - Delete a video
- `GET /api/settings/timelapse` / `POST /api/settings/timelapse` - Read/write config

## Home Assistant Integration

MQTT Discovery integration for Home Assistant:

**Architecture:**
- **Service:** `web/service/homeassistant.py` - `HomeAssistantService` class
- **Integration:** Started by `MqttQueue`; uses paho-mqtt for HA broker connection

**Publishes (sensors/entities):**
- Print progress, status, filename, speed, layer
- Nozzle/bed temperature and targets
- Time elapsed/remaining
- MQTT connected, PPPP connected (binary sensors)
- Printer light (switch, bidirectional — HA can turn light on/off)
- Camera entity (MJPEG)

**API endpoints:**
- `GET /api/settings/mqtt` / `POST /api/settings/mqtt` - Read/write HA config

**Configuration:** `HA_MQTT_*` environment variables (see above), or via Setup tab in web UI.

## Filament Profiles

SQLite-backed filament profile manager:

**Architecture:**
- **Store:** `web/service/filament.py` - `FilamentStore` class (not a Service; attached as `app.filaments`)
- **Storage:** `~/.config/ankerctl/filament.db` (SQLite)
- **UI Tab:** `static/tabs/filaments.html` — between History and Timelapse in the navbar

**Behavior:**
- Pre-seeded with 4 default profiles (Generic PLA, PETG, ABS, TPU) when the database is empty
- Full CRUD (create, read, update, delete) and duplicate operations
- Preheat action sends `M104 S<nozzle_temp_other_layer>` and `M140 S<bed_temp_other_layer>` to the printer via MQTT
- Schema auto-migrates on startup; existing databases gain new columns via `ALTER TABLE`

**API endpoints:**
- `GET /api/filaments` — list all profiles
- `POST /api/filaments` — create profile (auth required)
- `PUT /api/filaments/<id>` — update profile (auth required)
- `DELETE /api/filaments/<id>` — delete profile (auth required)
- `POST /api/filaments/<id>/apply` — preheat printer to profile temperatures (auth required)
- `POST /api/filaments/<id>/duplicate` — duplicate profile (auth required)

## Printer Selector

Multi-printer support with a navbar dropdown:

**Behavior:**
- The navbar shows a dropdown listing all configured printers as `{name} ({sn[-5:]})` when more than one printer is configured; shown as static text for a single printer
- Active printer selection is persisted to `default.json` as `active_printer_index` on the `Config` dataclass
- `PRINTER_INDEX` env var overrides the selector: the dropdown is disabled and a lock icon is shown
- Switching printers restarts all services to reconnect to the new printer
- Switching is blocked (409) while a print is active

**API endpoints:**
- `GET /api/printers` — return list of printers with `active_index` and `locked` flag
- `POST /api/printers/active` — switch active printer; JSON body `{"index": N}` (auth required)

## Debug Tab (Development Mode)

Enable by setting `ANKERCTL_DEV_MODE=true`. A "Debug" tab appears in the web UI.

**Sections:**
- **State Inspector** — Live JSON dump of `MqttQueue.get_state()` (print state + timelapse)
- **Controls** — Toggle verbose MQTT payload logging (`set_debug_logging()`)
- **Simulation** — Fire synthetic events: start, finish, fail, progress, temperature, speed, layer
- **Services** — Live service health panel (state, refs, restart button) — auto-refreshes every 5s
- **Log Viewer** — File picker + level/text filter over log files from `ANKERCTL_LOG_DIR`; auto-refresh every 5s

**API endpoints (only registered when `ANKERCTL_DEV_MODE=true`):**
- `GET /api/debug/state` - MqttQueue state JSON
- `POST /api/debug/config` - Set `debug_logging` flag
- `POST /api/debug/simulate` - Fire simulated event (`type`, `payload`)
- `GET /api/debug/services` - Service health summary
- `POST /api/debug/services/<name>/restart` - Restart a service
- `GET /api/debug/logs` - List log files
- `GET /api/debug/logs/<filename>` - Tail log file (`?lines=N`, default 500)
- `GET /api/debug/bed-leveling` - Read bed leveling grid (delegates to `_read_bed_leveling_grid()`)

**Security:** All `/api/debug/*` endpoints require authentication when an API key is configured.

## Bed Level Map

Reads the 7×7 bilinear bed leveling compensation grid from the printer via GCode `M420 V`.

**Architecture:**
- **Public endpoint:** `GET /api/printer/bed-leveling` — opens a short-lived MQTT connection, sends `M420 V` with a 4-second drain window, parses `BL-Grid-*` lines, returns grid + min/max/rows/cols as JSON. Available without Dev Mode.
- **Last-saved endpoint:** `GET /api/printer/bed-leveling/last` — returns the most recent saved grid from `ANKERCTL_LOG_DIR/bed_leveling/YYYYMMDD_HHMMSS.bed`.
- **Debug endpoint:** `GET /api/debug/bed-leveling` — same implementation, registered only when `ANKERCTL_DEV_MODE=true`.
- **Frontend:** Setup tab → Tools section — renders the grid as a colour-coded heatmap (blue=low, red=high), supports before/after snapshot comparison (snapshots stored in `localStorage`).

**Response format:**
```json
{
    "grid": [[0.1, -0.2, ...], ...],
    "min": -0.767,
    "max": 0.433,
    "rows": 7,
    "cols": 7,
    "saved_at": "20260224_153012"  // only in /last response
}
```

**MQTT notifications during G29:**
- `commandType 1007` — emitted once per probe point; `value` = current point index (total = 50: 1 initial center probe + 7×7 grid). Used to display a live auto-leveling progress bar.

**Notes:**
- Takes up to ~15 seconds; do not call during an active print.
- Grid rows are rendered bottom-to-top so Row 0 (printer front) appears at the bottom of the heatmap.
- Each successful query is saved to `ANKERCTL_LOG_DIR/bed_leveling/YYYYMMDD_HHMMSS.bed` as JSON.

## Docker

### Build and Run

```bash
docker compose up                    # Build and start
docker compose up --build            # Force rebuild
docker compose down                  # Stop
```

### Docker Networking

**CRITICAL:** Docker deployment requires `network_mode: host` due to PPPP's asymmetric UDP protocol. This currently limits Docker support to Linux hosts only.

### Multi-Architecture Support

CI builds for: `linux/arm/v7`, `linux/arm64`, `linux/amd64`

### Volume Mounts

- Configuration: `/home/ankerctl/.config/ankerctl` (maps to host config)
- SSL certificates: `/app/ssl`
- Log files: `/logs` (mapped when `ANKERCTL_LOG_DIR=/logs`)
- Timelapse captures: `/captures` (mapped when using `TIMELAPSE_CAPTURES_DIR=/captures`)

### Health Check

`GET /api/health` returns `{"status": "ok"}` with HTTP 200. No auth required.
The `HEALTHCHECK` in `Dockerfile` resolves `FLASK_HOST` (`0.0.0.0`/`::` → `127.0.0.1`).

## Common Tasks

### Adding a New CLI Command

1. Add command function in appropriate module (`cli/mqtt.py`, `cli/pppp.py`, etc.)
2. Register with Click decorator (`@group.command()`)
3. Use `@pass_env` for environment access
4. Follow existing patterns for consistency

### Adding a New MQTT Command Type

1. Check if type exists in `libflagship/mqtt.py` (MqttMsgType enum)
2. If new type needed, add to `specification/mqtt.stf` and run `make update`
3. Implement handler following existing patterns

### Adding a New Web Route

1. Add Flask route function in `web/__init__.py`
2. If it modifies state, make it POST/DELETE (auth enforced automatically)
3. If it's a GET that should require auth, add path to `_PROTECTED_GET_PATHS`
4. If it's a debug-only route, add inside the `ANKERCTL_DEV_MODE` block at the bottom

### Adding a New Web Service

1. Create `web/service/<name>.py` inheriting from `Service` (from `web/lib/service.py`)
2. Implement `worker_init()`, `worker_start()`, `worker_run(timeout)`, `worker_stop()`
3. Register via `app.svc.register("<name>", MyService())` in `register_services()` in `web/__init__.py`
4. Access from Flask routes using `with app.svc.borrow("<name>") as svc:`

### Adding a Debug API Endpoint

Add inside the `if os.getenv("ANKERCTL_DEV_MODE", ...) == "true":` block at the bottom of `web/__init__.py`.
Add the path (or prefix) to `_PROTECTED_GET_PATHS` or rely on the `is_debug_path` prefix check already present in `_check_api_key()`.

### Modifying Protocol Definitions

1. Edit specification files in `specification/*.stf`
2. Modify templates in `templates/` if structural changes needed
3. Run `make diff` to preview changes
4. Run `make update` to regenerate code
5. Test with CLI and web UI

## Commit and PR Guidelines

- Use short, descriptive commit messages (sentence case)
- Mention affected area (e.g., "Fix PPPP file upload reply handling")
- Keep commits focused on single changes
- Include testing notes and screenshots for UI changes

## Security Notes

- Configuration files contain sensitive authentication tokens
- Use `--insecure/-k` flag only for debugging, never in production
- Never commit `login.json` or expose `user_id`/`auth_token` values
- The MQTT `RECOVER_FACTORY` command requires `--force` flag as a safety measure
- Log viewer (`/api/debug/logs/<filename>`) has path-traversal protection (rejects `/`, `\`, `..`)
