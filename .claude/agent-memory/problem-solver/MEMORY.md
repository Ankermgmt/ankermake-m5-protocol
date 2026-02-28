# Problem Solver Agent Memory

## Key Architectural Patterns

### Video/Timelapse Interaction
- `VideoQueue` uses a simple boolean `video_enabled` flag, no reference counting
- Timelapse captures use ffmpeg against the local `/video` HTTP endpoint (not direct frame access)
- Both browser WebSocket (`/ws/video`) and timelapse HTTP (`/video`) consume from the same `VideoQueue` stream
- Known bug: timelapse can kill user-enabled video when print ends (Case 3 race condition)
- Fix approach: generation counter on `VideoQueue._enable_generation` to detect external re-enables

### Service Architecture
- Services managed by `ServiceManager` (`app.svc`) with borrow/get/put pattern
- `VideoQueue` extends `Service` base class with `worker_init/start/run/stop` lifecycle
- PPPP connection shared via `app.svc.get("pppp")` reference counting

### Key File Locations
- Video service: `web/service/video.py` (VideoQueue, profiles)
- Timelapse: `web/service/timelapse.py` (capture, ffmpeg assembly)
- MQTT service: `web/service/mqtt.py` (print state machine, event dispatch)
- Flask routes: `web/__init__.py` (WebSocket handlers, REST API)
- Generated files (DO NOT EDIT): `libflagship/mqtt.py`, `libflagship/pppp.py`, `libflagship/amtypes.py`, `static/libflagship.js`

## Common Analysis Patterns
- When analyzing state management bugs, trace the full lifecycle: enable -> state change by another actor -> disable
- Check for boolean flags that should be reference counts
- WebSocket handlers in `__init__.py` lines 207-259 control video/light via `videoqueue`
