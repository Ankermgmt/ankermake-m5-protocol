# Feature Roadmap — Implementation Plan

This file contains the implementation plan for the remaining phases of the `ankerctl` feature roadmap, specifically Phase 6.

6 features across 6 phases. All phases are **COMPLETE**.

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

## Phase 6 — Home Assistant MQTT Discovery (COMPLETED)

### Implementation

- **New file:** `web/service/homeassistant.py` — HA MQTT Discovery service
- **Modified:** `web/service/mqtt.py` — forwards printer data to HA service
- **Modified:** `.env.example` — new HA environment variables

### Architecture

- Connects to an external MQTT broker (HA's Mosquitto), separate from the printer's internal MQTT
- Publishes HA MQTT Discovery config payloads for automatic entity creation
- State published as retained JSON to `ankerctl/<printer_sn>/state`
- Uses LWT (Last Will and Testament) for automatic offline detection
- Light switch is bidirectional: HA can control the printer light

### Entities

| Entity ID | HA Type | Source |
|-----------|---------|--------|
| `print_progress` | `sensor` (%) | Command 0x03e9 |
| `print_status` | `sensor` (enum) | Derived |
| `nozzle_temp` | `sensor` (°C) | Command 0x03eb |
| `nozzle_temp_target` | `sensor` (°C) | Command 0x03eb |
| `bed_temp` | `sensor` (°C) | Command 0x03ec |
| `bed_temp_target` | `sensor` (°C) | Command 0x03ec |
| `print_speed` | `sensor` (mm/s) | Command 0x03ee |
| `print_layer` | `sensor` | Command 0x041c |
| `print_filename` | `sensor` | Command 0x03e9 |
| `time_elapsed` | `sensor` (s) | Command 0x03e9 |
| `time_remaining` | `sensor` (s) | Command 0x03e9 |
| `camera` | `camera` | MQTT image topic |
| `light` | `switch` | Command topic |
| `mqtt_connected` | `binary_sensor` | Internal |
| `pppp_connected` | `binary_sensor` | Internal |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HA_MQTT_ENABLED` | `false` | Enable HA MQTT Discovery |
| `HA_MQTT_HOST` | `localhost` | HA MQTT broker host |
| `HA_MQTT_PORT` | `1883` | HA MQTT broker port |
| `HA_MQTT_USER` | *(unset)* | MQTT username |
| `HA_MQTT_PASSWORD` | *(unset)* | MQTT password |
| `HA_MQTT_DISCOVERY_PREFIX` | `homeassistant` | HA discovery topic prefix |
| `HA_MQTT_TOPIC_PREFIX` | `ankerctl` | State topic prefix |
