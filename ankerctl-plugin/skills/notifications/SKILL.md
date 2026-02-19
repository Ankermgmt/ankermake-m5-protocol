---
name: notifications
description: Aktiviere bei Notification-Entwicklung, Apprise-Integration, Print-Events, oder wenn "Apprise", "notification", "PRINT_STARTED", "PRINT_FINISHED" erwähnt wird.
version: 1.0.0
---

# Notifications Skill (Apprise)

## Architektur

| Komponente | Datei |
|------------|-------|
| HTTP Client | libflagship/notifications/apprise_client.py |
| Events | libflagship/notifications/events.py |
| Notifier | web/notifications.py |
| Hooks | web/service/mqtt.py |

## Events

- `PRINT_STARTED` - Druck gestartet
- `PRINT_FINISHED` - Druck abgeschlossen
- `PRINT_FAILED` - Druck fehlgeschlagen
- `GCODE_UPLOADED` - G-code hochgeladen
- `PRINT_PROGRESS` - Fortschritt (konfigurierbares Intervall)

## Konfiguration (Environment Variables)

```bash
# Core settings
APPRISE_ENABLED=true
APPRISE_SERVER_URL=http://host:8000
APPRISE_KEY=ankerctl
APPRISE_TAG=critical

# Event toggles
APPRISE_EVENT_PRINT_STARTED=true
APPRISE_EVENT_PRINT_FINISHED=true
APPRISE_EVENT_PRINT_FAILED=true
APPRISE_EVENT_GCODE_UPLOADED=true
APPRISE_EVENT_PRINT_PROGRESS=true

# Progress settings
APPRISE_PROGRESS_INTERVAL=25         # Progress interval (%)
APPRISE_PROGRESS_INCLUDE_IMAGE=false # Attach snapshots
APPRISE_SNAPSHOT_QUALITY=hd          # 'sd' or 'hd'
APPRISE_SNAPSHOT_FALLBACK=true       # Fallback to G-code preview
APPRISE_PROGRESS_MAX=0               # Override progress scale (0=auto)
```

## Attachments

- **Live camera snapshots**: Requires `ffmpeg` + active PPPP connection
- **G-code preview images**: Fallback when live snapshot unavailable

## Configuration Storage

- Web UI: Setup → Notifications tab
- Environment variables (Docker deployments)
- Stored in `default.json` under `notifications.apprise`

## Adding a New Event

1. Add event constant in `libflagship/notifications/events.py`
2. Add environment variable toggle
3. Implement hook in `web/service/mqtt.py`
4. Call notifier from the appropriate service
