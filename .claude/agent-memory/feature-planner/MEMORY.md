# Feature Planner Memory

## Project Architecture (verified 2026-02-19)
- Services registered in `web/__init__.py` via `register_services()`: pppp, videoqueue, mqttqueue, filetransfer
- ServiceManager in `web/lib/service.py` — Thread-based with states: Starting/Running/Stopping/Stopped
- Debug menu gated by `ANKERCTL_DEV_MODE=true` env var, registered at module level (line 870)
- Debug endpoints: `/api/debug/state`, `/api/debug/config`, `/api/debug/simulate`, `/api/debug/logs`
- MqttQueue has `get_state()`, `simulate_event()`, `set_debug_logging()` methods
- PPPPService exposes `connected` property; VideoQueue has `video_enabled`, `last_frame_at`
- HomeAssistantService has `_state` dict, `_connected` flag

## Debug Menu Current State
- State Inspector: raw JSON dump of MqttQueue state only (7 fields)
- Controls: debug logging toggle + placeholder "Force Close Orphans" button
- Simulation: start/finish/fail events only
- Log Viewer: file picker + auto-refresh, reads from ANKERCTL_LOG_DIR

## Key Patterns
- Frontend uses Cash.js (jQuery-like), Bootstrap 5, Chart.js
- No new JS frameworks allowed
- WebSocket pattern: AutoWebSocket class with auto-reconnect
- Debug modal uses Bootstrap tabs inside a `modal-lg modal-dialog-scrollable`
- `app.svc.borrow(name)` context manager for safe service access
