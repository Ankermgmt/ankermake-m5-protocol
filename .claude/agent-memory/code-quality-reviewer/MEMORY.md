# Code Quality Reviewer - Agent Memory

## Project Conventions (Confirmed)
- 4-space indentation in Python; `snake_case` for functions/vars, `CapWords` for classes
- Import order: stdlib -> third-party -> local (but frequently violated in recent commits)
- Logging: `log = logging.getLogger("<module>")` per module; some files use `import logging as log` (inconsistent)
- CLI: Click decorators with `@pass_env`; `Environment` object for shared state
- Frontend: Cash.js (`$()`) for DOM; Bootstrap 5.3 for UI; JMuxer for video
- Auto-generated files (DO NOT REVIEW): `libflagship/mqtt.py`, `libflagship/pppp.py`, `libflagship/amtypes.py`, `static/libflagship.js`

## Architecture Notes
- `web/lib/service.py`: Thread-based service framework; `Service` extends `Thread`; `ServiceManager` handles lifecycle
- Services: pppp, videoqueue, mqttqueue, filetransfer - registered in `register_services()`
- WebSocket routes: `/ws/mqtt`, `/ws/video`, `/ws/pppp-state`, `/ws/ctrl`, `/ws/upload`
- Config stored in `~/.config/ankerctl/default.json`; `ConfigManager` with `.open()` context and `.modify()` for writes
- MQTT temps come as value * 100 (divide by 100 for Celsius)

## Known Issues / Anti-patterns
- `cli/model.py` Serialize.from_dict has dead code (first loop never used, overwritten by second loop)
- `web/service/timelapse.py` reload_config() previously re-created `_lock`, `_stop_event`, `_capture_thread` - fixed in recent commits
- Debug endpoints (`/api/debug/*`) have no auth gate beyond env var check in template rendering
- Multiple places duplicate ffmpeg snapshot logic (notifications.py, timelapse.py, web/__init__.py)
- `web/service/history.py` creates new SQLite connections per operation (no connection pooling)
- Print history uses `datetime.utcnow()` which is deprecated in Python 3.12+
- `video.py` `api_light_state` sets `saved_light_state` before PPPP null check -- saved state may not reflect hardware

## Timelapse (Reviewed 2026-02-21)
- Two light modes: "session" (on at start, off at finish) and "snapshot" (on/off per frame)
- BUG: snapshot mode hardcodes `api_light_state(False)` instead of restoring original state
- BUG: `_finalize` closure writes `_current_dir`/`_current_filename`/`_frame_count` outside lock (race with start_capture)
- `saved_light_state` on VideoQueue is only set by API calls, not queried from hardware -- always starts as None
- Snapshot mode adds 2.5s hard sleep per frame; thread join timeout is only 5s -- may leave threads dangling
- ROOT CAUSE of delayed video: `finish_capture()` ALWAYS uses 60-min resume timer (`_RESUME_WINDOW_SEC=3600`)
  even on normal print completion. No distinction between pause and finish. Fix: add `final=True` param.
- `fail_capture()` calls `_assemble_video()` while holding `self._lock` -- blocks for up to 120s (ffmpeg timeout)
- Frontend: timelapse gallery only loads on tab show event, no polling -- user must switch tabs to see new videos
- FPS formula: `frame_count // 30` stays at 1 fps until 60+ frames due to integer division

## Security Observations
- API key auth middleware is solid: session cookies, X-Api-Key header, query param with redirect
- Debug endpoints accessible without auth if ANKERCTL_DEV_MODE is set
- Timelapse filename sanitization in `_assemble_video` is basic but adequate
- Log viewer has path traversal protection (checks for `/`, `\`, `..` in filename)
- XSS risk in history tab: `e.filename` rendered via string interpolation into HTML (jQuery `.append()`)

## File Locations
- Main entry: `/ankerctl.py`
- Web app: `/web/__init__.py` (Flask routes + WebSocket handlers)
- MQTT service: `/web/service/mqtt.py` (MqttQueue - core print tracking logic)
- History: `/web/service/history.py` (SQLite-backed)
- Timelapse: `/web/service/timelapse.py` (ffmpeg-based)
- HA integration: `/web/service/homeassistant.py` (paho-mqtt)
- Notifications: `/web/notifications.py` (Apprise client wrapper)
- Frontend JS: `/static/ankersrv.js`
- Base template: `/static/base.html`
