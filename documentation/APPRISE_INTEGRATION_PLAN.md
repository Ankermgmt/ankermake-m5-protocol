# Apprise Integration for ankerctl (External Server)

## Goals
- Send notifications via an external Apprise API server (no Apprise library dependency).
- Persist settings in `default.json` under `notifications.apprise`.
- Support Docker environment overrides (`APPRISE_*`).
- Add configuration UI in the Setup tab with a side navigation (Printer / Notifications).
- Keep UI strings in English for now; translations later.

## Events
- `print_started`
- `print_finished`
- `print_failed`
- `gcode_uploaded`
- `print_progress` (interval-based)

## Config schema (`default.json`)
```json
{
  "account": { "...": "..." },
  "printers": [ { "...": "..." } ],
  "notifications": {
    "apprise": {
      "enabled": false,
      "server_url": "",
      "key": "",
      "tag": "",
      "events": {
        "print_started": true,
        "print_finished": true,
        "print_failed": true,
        "gcode_uploaded": true,
        "print_progress": true
      },
      "progress": {
        "interval_percent": 25,
        "include_image": false,
        "snapshot_quality": "hd"
      },
      "templates": {
        "print_started": "Print started: {filename}",
        "print_finished": "Print finished: {filename} ({duration})",
        "print_failed": "Print failed: {filename} ({reason})",
        "gcode_uploaded": "Upload complete: {filename} ({size})",
        "print_progress": "Progress: {percent}% - {filename}"
      }
    }
  }
}
```

Important: when `config import` runs, it must **merge** existing `notifications.apprise` instead of overwriting it.

## Docker environment overrides
```bash
APPRISE_ENABLED=true
APPRISE_SERVER_URL=http://apprise:8000
APPRISE_KEY=ankerctl
APPRISE_TAG=critical

APPRISE_EVENT_PRINT_STARTED=true
APPRISE_EVENT_PRINT_FINISHED=true
APPRISE_EVENT_PRINT_FAILED=true
APPRISE_EVENT_GCODE_UPLOADED=false
APPRISE_EVENT_PRINT_PROGRESS=true

APPRISE_PROGRESS_INTERVAL=25
APPRISE_PROGRESS_INCLUDE_IMAGE=false
APPRISE_SNAPSHOT_QUALITY=hd
```

## Integration points (repo layout)
```
libflagship/
  notifications/
    __init__.py
    apprise_client.py  # HTTP-only client
    events.py          # Event enum + payload helpers

web/
  __init__.py          # /api/notifications/* endpoints
  service/mqtt.py      # emit print events from MQTT messages
  service/filetransfer.py  # emit gcode_uploaded

static/
  tabs/setup.html      # Setup tab sections + side nav
  ankersrv.js          # load/save/test settings
```

## UI plan (Setup tab)
- Keep everything in the existing Setup tab.
- Add a left-side list-group nav on desktop:
  - Printer
  - Notifications
- Each section uses an anchor `id` so the nav scrolls to it.
- On mobile, collapse the nav into a single button or keep it as a top list.
- All UI labels remain English for now.

## Implementation steps (proposed)
1. Add `notifications.apprise` defaults + merge logic in config import.
2. Implement `AppriseClient` (HTTP-only) with env overrides.
3. Add API routes:
   - `GET /api/notifications/settings`
   - `POST /api/notifications/settings`
   - `POST /api/notifications/test`
4. Add Setup UI + JS (load/save/test).
5. Hook events:
   - `print_started/finished/failed/progress` from MQTT.
   - `gcode_uploaded` from file transfer completion.
6. Optional phase 2: snapshot attachment for progress/finish.

## Notes / open questions
- Determine the most reliable MQTT fields for start/finish/fail state.
- Decide whether notifications should also run in CLI-only mode (outside webserver).
