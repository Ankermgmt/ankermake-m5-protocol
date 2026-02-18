# Project Status & Handover Documentation

**Last Updated:** 2026-02-18
**Project:** AnkerMake M5 Protocol (ankerctl)
**Current State:** Feature Phases 1–5 Complete

This document tracks the progress of the `ankerctl` feature roadmap and provides instructions for the next steps (Phase 6).

---

## ✅ Completed Features

### Phase 1: Quick Wins
- **Tab Title:** Updates dynamically with print progress.
- **Presets:** Added TPU custom heat preset.
- **Snapshot:** Button to download current camera frame.

### Phase 2: GCode Console
- **Implementation:** New card in Home tab.
- **Features:** File upload (`.gcode`) and raw PID/GCode command sending.
- **Backend:** `web.service.mqtt` handles command injection.

### Phase 3: Print History
- **Implementation:** SQLite-backed service (`web/service/history.py`).
- **DB Location:** `~/.config/ankerctl/history.db`.
- **UI:** History tab with pagination and "Clear" function.
- **Hooks:** Automatically records start/finish/fail events.

### Phase 4: Temperature Graph
- **Implementation:** Client-side only (Chart.js v4).
- **UI:** Interactive graph in Home tab with selectable time windows (5m–1h).
- **Data:** Uses existing WebSocket streams (Command 1003/1004).

### Phase 5: Timelapse
- **Implementation:** `web/service/timelapse.py`.
- **Process:** Captures MJPEG frames every 30s -> ffmpeg assembly -> .mp4.
- **Storage:** Persisted to `/captures` (docker volume).
- **Management:** Gallery UI in History tab; auto-pruning of old videos.

---

## 🚧 Next Steps: Phase 6 (Home Assistant MQTT)

The goal of Phase 6 is to allow `ankerctl` to act as a bridge to Home Assistant (HA) via MQTT Discovery.

### Tasks to Implement

1.  **Create `web/service/homeassistant.py`**
    -   Connect to an *external* MQTT broker (HA's broker), distinct from the printer's internal MQTT.
    -   Implement MQTT Discovery protocol: publish config payloads to `homeassistant/sensor/...`.
    -   Entities needed: Print status, progress, temps (nozzle/bed), speed, layer, filename, camera, light switch.

2.  **Modify `web/service/mqtt.py`**
    -   Inject the HA service.
    -   In `_handle_notification`, forward relevant data (temps, status changes) to the HA service to publish state updates.

3.  **Configuration**
    -   Add Envrionment variables for HA broker connection (`HA_MQTT_HOST`, `HA_MQTT_USER`, etc.).

### Reference Implementation Plan

See `implementation_plan.md` (Artifact) or the details below for the exact schema.

**Env Vars Needed:**
- `HA_MQTT_ENABLED` (default: false)
- `HA_MQTT_HOST`
- `HA_MQTT_PORT`
- `HA_MQTT_USER`
- `HA_MQTT_PASSWORD`
- `HA_MQTT_DISCOVERY_PREFIX` (default: `homeassistant`)

---

## 📂 Key Files Created/Modified

- `web/service/history.py` (New: History service)
- `web/service/timelapse.py` (New: Timelapse service)
- `web/service/mqtt.py` (Modified: Event hooks)
- `static/ankersrv.js` (Modified: Chart.js logic, Timelapse gallery)
- `static/tabs/history.html` (Modified: History & Timelapse UI)
- `static/tabs/home.html` (Modified: Temp Graph, GCode Console)
- `docker-compose.yaml` (Modified: Volumes)
- `.env.example` (Updated)

---

## 🛠️ How to Continue

1.  **Start Phase 6**: Create `web/service/homeassistant.py`.
2.  **Dependencies**: No new Python deps should be needed (using `paho-mqtt` or similar if not already present, otherwise `libflagship` might have MQTT utils, but standard `paho-mqtt` is likely best for the external connection).
3.  **Testing**: Use a local MQTT broker (e.g., Mosquitto) to verify discovery messages.
