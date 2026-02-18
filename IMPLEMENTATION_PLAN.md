# Feature Roadmap — Implementation Plan

This file contains the implementation plan for the remaining phases of the `ankerctl` feature roadmap, specifically Phase 6.

6 features across 6 phases. Phases 1–5 are **COMPLETE**. Phase 6 is **PENDING**.

---

## Phase 1 — Quick Wins ✅ (COMPLETED)
- **Tab-Title**: Shows print progress (e.g., "🖨️ 45% | ankerctl").
- **TPU Preset**: Added TPU button (230°C/50°C) to Home tab.
- **Snapshot**: Added snapshot download button to Video Controls.

## Phase 2 — GCode Console ✅ (COMPLETED)
- **UI**: Added "GCode Console" card to Home tab.
- **Functionality**: Upload `.gcode` files or send raw GCode commands.
- **Backend**: API `/api/printer/gcode` handles commands.

## Phase 3 — Print History ✅ (COMPLETED)
- **Service**: `web/service/history.py` (SQLite).
- **Storage**: `~/.config/ankerctl/history.db`.
- **Integration**: Records start/finish/fail events from MQTT.
- **UI**: "Print History" tab with table and clear button.
- **Config**: `PRINT_HISTORY_RETENTION_DAYS` (90), `PRINT_HISTORY_MAX_ENTRIES` (500).

## Phase 4 — Temperatur-Grafik ✅ (COMPLETED)
- **UI**: Chart.js graph in Home tab.
- **Data**: Client-side ring buffer (1h history) from WebSocket stream (command 1003/1004).
- **Features**: 4 datasets (Nozzle/Bed Current/Target), configurable time window.

## Phase 5 — Timelapse ✅ (COMPLETED)
- **Service**: `web/service/timelapse.py`.
- **Logic**: Captures snapshots every 30s (configurable), assembles with `ffmpeg`.
- **Storage**: `/captures` (mapped volume).
- **UI**: Gallery in History tab with download/delete actions.
- **Config**: `TIMELAPSE_ENABLED`, `TIMELAPSE_INTERVAL_SEC`, `TIMELAPSE_MAX_VIDEOS`.

---

## Phase 6 — Home Assistant MQTT Discovery (PENDING)

### Goal
 Integrate with Home Assistant via MQTT Discovery, allowing the printer to appear as a device with sensors, camera, and controls in HA.

### New files

#### [NEW] [web/service/homeassistant.py](file:///home/django01/Development/ankermake-m5-protocol/ankermake-m5-protocol/web/service/homeassistant.py)

HA MQTT Discovery service:

- Connect to HA MQTT broker (separate from printer MQTT)
- Publish discovery config messages to `<discovery_prefix>/sensor|camera|switch|binary_sensor/<node_id>/<object_id>/config`
- Periodically publish state updates to `ankerctl/<printer_sn>/state`
- Entities: see table below
- On shutdown: publish empty config to remove entities (or set `availability` to offline)

**Entities:**

| Entity ID | HA Type | MQTT commandType |
|-----------|---------|-----------------|
| `print_progress` | `sensor` (%) | 1001 |
| `print_status` | `sensor` (enum) | derived |
| `nozzle_temp` | `sensor` (°C) | 1003 |
| `nozzle_temp_target` | `sensor` (°C) | 1003 |
| `bed_temp` | `sensor` (°C) | 1004 |
| `bed_temp_target` | `sensor` (°C) | 1004 |
| `print_speed` | `sensor` (mm/s) | 1006 |
| `print_layer` | `sensor` | 1052 |
| `print_filename` | `sensor` | 1001 |
| `time_elapsed` | `sensor` | 1001 |
| `time_remaining` | `sensor` | 1001 |
| `camera` | `camera` | MJPEG stream URL |
| `light` | `switch` | GCode M106/M107 |
| `mqtt_connected` | `binary_sensor` | internal |
| `pppp_connected` | `binary_sensor` | internal |

#### [MODIFY] [web/service/mqtt.py](file:///home/django01/Development/ankermake-m5-protocol/ankermake-m5-protocol/web/service/mqtt.py)

Forward parsed MQTT data to HA service for state publishing.

#### [MODIFY] [__init__.py](file:///home/django01/Development/ankermake-m5-protocol/ankermake-m5-protocol/web/__init__.py)

Register HA service, conditionally started based on env vars.

### New env vars

| Variable | Default | Description |
|----------|---------|-------------|
| `HA_MQTT_ENABLED` | `false` | Enable HA MQTT Discovery |
| `HA_MQTT_HOST` | `localhost` | HA MQTT broker host |
| `HA_MQTT_PORT` | `1883` | HA MQTT broker port |
| `HA_MQTT_USER` | *(unset)* | MQTT username |
| `HA_MQTT_PASSWORD` | *(unset)* | MQTT password |
| `HA_MQTT_DISCOVERY_PREFIX` | `homeassistant` | HA discovery topic prefix |
| `HA_MQTT_TOPIC_PREFIX` | `ankerctl` | State topic prefix |
