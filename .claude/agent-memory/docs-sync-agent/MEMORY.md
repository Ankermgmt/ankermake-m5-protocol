# Docs Sync Agent Memory — ankerctl

## Sections in CLAUDE.md That Frequently Drift

- **Directory Structure**: `web/service/` expansion is often incomplete. Always include `history.py`, `homeassistant.py`, `timelapse.py`, `web/lib/service.py`, and `web/notifications.py`.
- **CLI Quick Reference**: `config set-password`, `config remove-password`, `config decode`, `mqtt send`, `mqtt gcode-dump`, and `http calc-*` commands are frequently missing.
- **Environment Variables**: Section grows with every new service. High-drift subsections: HA_MQTT_*, TIMELAPSE_*, ANKERCTL_DEV_MODE, ANKERCTL_LOG_DIR, FLASK_SECRET_KEY, UPLOAD_MAX_MB.
- **Debug Tab section**: Endpoint list needs updating whenever new /api/debug/* routes are added.

## Known Accurate Sections (Less Frequent Review Needed)

- Architecture overview (three-tier)
- Build System / Generated Files / Makefile Commands
- Protocol Reference (MQTT topics, common commands table)
- Docker Networking (network_mode: host constraint)
- Coding Style and Conventions

## MQTT_COMMANDS.md

- As of Feb 2026: 44 command types in the enum, all documented.
- The enum is in `libflagship/mqtt.py` (generated file — check `specification/mqtt.stf` for source).
- Missing entries found and added in Feb 2026 audit: `RESET_GCODE_PARAM`, `DEVICE_LOG_UPLOAD`, `ONOFF_MODAL`, `PREHEAT_CONFIG`, `ADVANCED_PARAMETERS`, `SYSTEM_CHECK`, `AI_INFO_CHECK`, `MODEL_LAYER`, `MODEL_DL_PROCESS`, `PRINT_MAX_SPEED`, `ALEXA_MSG`.
- Feb 2026 second audit: added "Printer Notification Types" section documenting unsolicited commandTypes 1000, 1001, 1003, 1004, 1006, 1007, 1044, 1052.
- ct=1007 (decimal) = 0x03ef = ZZ_MQTT_CMD_AUTO_LEVELING: emitted per probe point during G29; value = current point index (49 total for 7x7 grid).
- ct=1072 (isLeveled) mentioned in some docs but NOT yet in the code — do not document until implemented.

## Key Agent Memory Sources

The most useful agent memories for understanding recent changes:
1. `coding-agent/MEMORY.md` — architecture decisions, logging, patterns
2. `code-quality-reviewer/MEMORY.md` — file locations, known anti-patterns, services list
3. `feature-planner/MEMORY.md` — debug menu state, API endpoints, service details
4. `.claude/agent-memory/MEMORY.md` (root) — covers coding agent conventions

## Features Added Since Initial README/CLAUDE.md

(All documented in CLAUDE.md as of Feb 2026 audit)
- Debug tab (`ANKERCTL_DEV_MODE=true`) with State Inspector, Controls, Simulation, Services, Log Viewer
- Timelapse capture service (`web/service/timelapse.py`) with dedicated UI tab
- Print History service (`web/service/history.py`, SQLite-backed)
- Home Assistant MQTT Discovery (`web/service/homeassistant.py`)
- Apprise notifications with live snapshot + light control (`APPRISE_SNAPSHOT_LIGHT`)
- API key auth (`ANKERCTL_API_KEY`, `config set-password`/`config remove-password`)
- File logging (`ANKERCTL_LOG_DIR`)
- Bed Level Map (Setup tab, GET /api/printer/bed-leveling, 7x7 heatmap, before/after snapshots)
- mqtt gcode-dump CLI command with --window and --drain options
- MQTT notification ct=1007: auto-leveling probe progress (value = current point, 49 total)
- Debug tab moved from modal to dedicated tab (static/tabs/debug.html)

## Environment Variable Accuracy Notes

- `UPLOAD_RATE_MBPS` choices are `5, 10, 25, 50, 100` and default is `10` (not 2/4/6/8 as was in old README/env.example).
- `APPRISE_SNAPSHOT_QUALITY` now also accepts `fhd` (1920x1080), not just `sd`/`hd`.
- `FLASK_SECRET_KEY` is optional but important for persistent sessions across restarts.
- `TIMELAPSE_LIGHT` env var (values: `snapshot` | `session` | unset) is defined in `cli/model.py:default_timelapse_config()`.

## README.md Drift Patterns

The README had these persistent gaps fixed in Feb 2026 audit:
- Missing features list items: Print History, Timelapse, Apprise, HA integration, API key auth, Debug tab
- Missing env vars: `FLASK_SECRET_KEY`, `PRINTER_INDEX`, `ANKERCTL_DEV_MODE`, `ANKERCTL_LOG_DIR`, `TIMELAPSE_LIGHT`, all `HA_MQTT_*` vars
- Missing sections: Print History, Timelapse detail (with light control and resume window), Home Assistant, Debug Tab
- Wrong `UPLOAD_RATE_MBPS` default and choices — also present in `.env.example` (fixed both)
- `APPRISE_SNAPSHOT_QUALITY` missing `fhd` option

## .env.example Accuracy Notes

- Also suffered from wrong UPLOAD_RATE_MBPS (2, 4, 6, 8) — fixed to (5, 10, 25, 50, 100), default 10.
- `TIMELAPSE_LIGHT` was missing from the Timelapse section — added with both valid values documented.
