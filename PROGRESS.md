# Project Status & Handover Documentation

**Last Updated:** 2026-02-18
**Project:** AnkerMake M5 Protocol (ankerctl)
**Current State:** Feature Phases 1–6 Complete

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

### Phase 6: Home Assistant MQTT Discovery
- **Implementation:** `web/service/homeassistant.py`.
- **Connection:** Connects to an external MQTT broker (HA's Mosquitto), separate from the printer's internal MQTT.
- **Discovery:** Publishes HA MQTT Discovery config payloads for automatic entity creation.
- **Entities:** 11 sensors (progress, status, temps, speed, layer, filename, times), 2 binary sensors (connectivity), 1 switch (light), 1 camera.
- **State:** Publishes JSON state to `ankerctl/<printer_sn>/state` with retained messages.
- **Light Control:** Subscribes to command topic for bidirectional light switch control from HA.
- **LWT:** Uses Last Will and Testament for automatic offline detection.
- **Config:** Environment variables (`HA_MQTT_ENABLED`, `HA_MQTT_HOST`, etc.).

---

## Key Files Created/Modified

- `web/service/history.py` (New: History service)
- `web/service/timelapse.py` (New: Timelapse service)
- `web/service/homeassistant.py` (New: Home Assistant MQTT Discovery)
- `web/service/mqtt.py` (Modified: Event hooks, HA data forwarding)
- `static/ankersrv.js` (Modified: Chart.js logic, Timelapse gallery)
- `static/tabs/history.html` (Modified: History & Timelapse UI)
- `static/tabs/home.html` (Modified: Temp Graph, GCode Console)
- `docker-compose.yaml` (Modified: Volumes)
- `.env.example` (Updated)
