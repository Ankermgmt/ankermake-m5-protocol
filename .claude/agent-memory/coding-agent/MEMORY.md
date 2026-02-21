# Coding Agent Memory - ankerctl

## Logging Architecture

- `cli/logfmt.py` is the single source of truth for logging setup.
- `setup_logging(level, log_dir)` configures all handlers. `log_dir` comes from `ANKERCTL_LOG_DIR` env var.
- Named loggers: `mqtt`, `web`, `history`, `timelapse`, `homeassistant` — each gets its own `*.log` file.
- Root logger (`ankerctl.log`) gets all output via propagation from named loggers.
- Format for named logs: `%(asctime)s [%(levelname)s]: %(message)s`
- Format for root/ankerctl.log: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
- Debug log viewer API: `GET /api/debug/logs` and `GET /api/debug/logs/<filename>` — only active when `ANKERCTL_DEV_MODE=true`.
- Log directory default for debug API: `os.getenv("ANKERCTL_LOG_DIR", "/logs")`.

## Key Files

- `ankerctl.py`: CLI entry point; calls `setup_logging` in the `main` Click group callback.
- `cli/logfmt.py`: Logging setup and formatters.
- `web/__init__.py`: Flask app; debug routes conditionally registered under `ANKERCTL_DEV_MODE`.
- `static/tabs/debug.html`: Debug tab UI with Log Viewer; filters on `[INFO]`, `[WARNING]`, etc.

## Generated Files (DO NOT EDIT)

`libflagship/mqtt.py`, `libflagship/pppp.py`, `libflagship/amtypes.py`, `static/libflagship.js`
Edit specs in `specification/*.stf` and run `make update` instead.

## Patterns

- CLI commands use `@pass_env` decorator; access shared state via `env` object.
- MQTT commands: use `MqttMsgType` enums and `client.command(cmd)` / `client.await_response(...)`.
- PPPP file transfer: use `FileUploadInfo.from_data(...)` and `pppp_send_file(...)`.

## MQTT Real Payload Facts (CONFIRMED from container logs)

- `ZZ_MQTT_CMD_PRINT_SCHEDULE` (ct 1001): sends `{"commandType":1001,"time":<remaining>,"totalTime":<elapsed>,"progress":<0-1000>,"name":"<filename>","task_id":"<uuid>","img":"<url>", ...}`.
  - `progress` is on a 0-1000 scale (NOT 0-100). Set `APPRISE_PROGRESS_MAX=1000` or use `_normalize_progress()`.
  - `time` = remaining seconds, `totalTime` = elapsed seconds.
- `ZZ_MQTT_CMD_MODEL_LAYER` (ct 1052): sends `{"commandType": 1052, "total_layer": N, "real_print_layer": M}`.
  - This is the correct source for layer-based progress — compute `Math.round(real_print_layer / total_layer * 100)`.
- `ZZ_MQTT_CMD_EVENT_NOTIFY` (ct 1000): state machine signals, `{"commandType":1000,"subType":1,"value":N}`.
  - value=0 = IDLE/print ended, value=1 = PRINT ACTIVE, value=7 = HEATING, value=8 = FILE UPLOADING.
  - ct 1044 (raw int, not in MqttMsgType enum): file upload info `{"commandType":1044,"filePath":"<full path>","url":"<preview url>"}`.
  - `os.path.basename(filePath)` gives the filename for history recording.
- `_normalize_progress()` in `web/service/mqtt.py` handles scaling for Apprise notifications (internal use only).
- `MqttQueue.worker_run()` calls `self.notify(obj)` — raw obj goes to WebSocket stream unchanged.
- `APPRISE_PROGRESS_MAX` env var: explicit divisor for progress; 0/unset = auto-detect.

## MQTT Message Flow (WebSocket to Frontend)

1. Printer sends ct 1001 with `time`, `totalTime`, `progress` (0-1000 scale), `name`, `task_id`; ct 1052 with layer counts.
2. `MqttQueue.worker_run()` receives raw payload dicts from `client.fetch()`.
3. `self.notify(obj)` sends raw obj to WebSocket stream (no frontend normalization needed).
4. `self._forward_to_ha(obj)` and `self._handle_notification(obj)` receive same raw obj.

## Print History State Machine (`web/service/mqtt.py`)

- ct 1044 handler: captures `self._last_filename`; if `_pending_history_start` is True, calls `record_start` here.
- ct 1000 value=1 handler: calls `record_start` only when `_last_filename` is set; else sets `_pending_history_start=True`.
- Legacy progress handler (~line 435): same pattern — only call `record_start(effective_filename, ...)` if truthy, else set pending flag.
- `_pending_history_start` is reset in `_reset_print_state()`.
- `_PLACEHOLDER_NAMES = frozenset({"unknown", "unknown.gcode", ""})` in `history.py` — `record_start()` returns None immediately for placeholders.
- `status='interrupted'` (NOT 'finished') used for orphaned open history entries on container restart.

## Timelapse Resume Window (`web/service/timelapse.py`)

- `_RESUME_WINDOW_SEC = 3600` (60 min) at module level.
- `_resume_dir`, `_resume_filename`, `_resume_frame_count`, `_finalize_timer` track pending assembly state.
- `finish_capture()` calls `_schedule_finalize()` (delayed timer) instead of assembling immediately.
- `start_capture(filename)` checks `_resume_filename == filename` — if match, resumes (reuses frame dir + count) via `_cancel_finalize_timer()`.
- `fail_capture()` calls `_cancel_pending_resume()` to discard frames and abort any timer before partial assembly.
- `_cancel_finalize_timer()` — cancels the threading.Timer only.
- `_cancel_pending_resume()` — cancels timer AND deletes the temp frame directory.

## MqttMsgType Values (IntEnum, from libflagship/mqtt.py — GENERATED, do not edit)

- `ZZ_MQTT_CMD_EVENT_NOTIFY = 0x03e8 = 1000`
- `ZZ_MQTT_CMD_PRINT_SCHEDULE = 0x03e9 = 1001`
- `ZZ_MQTT_CMD_NOZZLE_TEMP = 0x03eb = 1003`
- `ZZ_MQTT_CMD_HOTBED_TEMP = 0x03ec = 1004`
- `ZZ_MQTT_CMD_PRINT_SPEED = 0x03ee = 1006`
- `ZZ_MQTT_CMD_MODEL_LAYER = 0x041c = 1052`

## Service Architecture

- `web/lib/service.py`: `Service` base class (Thread + state machine). `notify()` broadcasts to handlers.
- `ServiceManager.stream()` taps a service and yields from a Queue for WebSocket streaming.
- `stream()` uses `queue.get(timeout=1.0)` with `_queue.Empty` catch to avoid blocking forever when service stops.
- `ServiceManager.svcs` is a plain dict — use `.get("name")` for safe lookup without incrementing refs.
- `ServiceManager.get("name")` increments `refs[name]` and calls `start()` if refs go from 0→1. Always pair with `put()`.

## VideoQueue Key Attributes (web/service/video.py)

- `video_enabled`: bool; controls whether `worker_start()` establishes a PPPP connection.
- `pppp`: PPPP service reference — is `None` if video_enabled=False at start time.
- `last_frame_at`: `time.monotonic()` timestamp updated on every VIDEO_FRAME received; `None` if no frame yet.
- `set_video_enabled(bool)`: cleanly enables/disables video and start/stops the service.
- Bug pattern: VideoQueue can be in RunState.Running with `pppp=None` if it was started while video_enabled=False.

## Debug API Pattern (ANKERCTL_DEV_MODE)

- All `/api/debug/*` GET endpoints are automatically protected by auth middleware (prefix check).
- Short-lived MQTT connections in debug endpoints: use `cli.mqtt.mqtt_open(config, printer_index, insecure)` + `cli.mqtt.mqtt_gcode_dump(client, gcode, collect_window=N)`.
- GCode dump responses: combine `msg.get("resData", "")` fields across all returned dicts, then parse line by line.
- Bed leveling debug endpoint `GET /api/debug/bed-leveling` delegates to `_read_bed_leveling_grid()`.

## Bed Level Map Feature (Setup > Tools tab)

- Public endpoint: `GET /api/printer/bed-leveling` (non-debug, regular GET — no auth required unless API key set).
- Shared helper `_read_bed_leveling_grid()` in `web/__init__.py` returns `(data_dict, None)` or `(None, (error_dict, status))`.
- `static/tabs/setup.html`: Bed Level Map card added as `col-lg-6` sibling of Auto-Leveling in Tools tab. Compare Snapshots collapsible section below as `col-12`.
- `static/ankersrv.js` `bedLevelRenderGrid(grid, min, max, targetId)` — 4th param selects target div (default: `"dbg-bedlevel-map-wrap"` for backward compat).
- Snapshot storage: `localStorage` key `ankerctl_bed_snapshots`, max 10 entries (`[{id, label, data}]`).
- Auto-level completion: `_onMqttStateChange(value)` hooked into ct=1000 MQTT handler. State: `false` → `true` → `"active"` (saw value=1) → triggers `bedLevelRead()` on value=0. 10-min timeout.
- `commandType 1000` now handled in MQTT WebSocket handler (was falling through to console.log before).

Notes:
- Agent threads always have their cwd reset between bash calls — always use absolute file paths.
- In your final response always share relevant file names and code snippets with absolute paths.
- Do not use emojis. Do not use a colon before tool calls.
