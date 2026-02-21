# Coding Agent Memory — ankerctl

## Key Architectural Notes
- `web/__init__.py` is the Flask app entry point; debug endpoints should be gated with `if os.getenv("ANKERCTL_DEV_MODE", "false").lower() == "true":` at module level
- `web/service/timelapse.py` `reload_config()` must NOT reset thread/lock state — only update config values
- Flask `send_file` streams lazily — use `@after_this_request` for temp file cleanup, not `finally`
- Service borrow context (`with app.svc.borrow(...) as svc:`) must contain ALL attribute accesses on the service; reads outside the block are a use-after-release bug

## Logging Convention
- Use `import logging` + `log = logging.getLogger(__name__)` (NOT `import logging as log`)
- Existing module-level loggers with explicit names (e.g. `logging.getLogger("mqtt")`) are acceptable

## Time Conventions
- Use `time.monotonic()` for all duration/elapsed calculations; `time.time()` only for wall-clock timestamps
- `datetime.utcnow()` is deprecated since Python 3.12 — use `datetime.now(timezone.utc).replace(tzinfo=None)` and import `timezone` from `datetime`

## XSS Prevention
- Always call `escapeHtml(str)` (implemented using `document.createTextNode`) before interpolating user data into HTML template literals in `ankersrv.js`

## Import Ordering
- `cli/model.py`: All stdlib imports (including `os`) must be at the top, before function/class definitions

## Dead Code
- `Serialize.from_dict()` previously had two identical loops — only one is needed (the second one that uses `data[k]` directly)

## Paho-MQTT v2
- Must pass `paho_mqtt.CallbackAPIVersion.VERSION1` as first arg to `paho_mqtt.Client()` to avoid deprecation warning

## Auth Middleware Pattern
- `_check_api_key()` is `@app.before_request` — GET/HEAD/OPTIONS allowed by default unless path in `_PROTECTED_GET_PATHS`
- For dynamic-segment debug routes: use `request.path.startswith("/api/debug/")` prefix check in addition to `_PROTECTED_GET_PATHS`
- All `/api/debug/*` endpoints must be protected when API key is configured

## Debug Tab Architecture (as of Feb 2026)
- Debug console is a dedicated nav tab (`#debug` pane), NOT a modal
- Only shown when `debug_mode` is True (from `inject_debug` context processor)
- JS scoped inside `if ($("#debug").length)` guard in ankersrv.js
- `renderSection(title, obj)` helper builds Bootstrap key-value tables with color-coded values
- Service health auto-refreshes every 5s when services pill is active; state auto-refreshes every 3s
- `simulate_event()` in `MqttQueue` supports: start, finish, fail, progress, temperature, speed, layer

## get_state() Structured Format
Returns `{"print": {...}, "debug_logging": bool, "timelapse": {...}}`
