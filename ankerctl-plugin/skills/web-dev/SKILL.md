---
name: web-dev
description: Aktiviere bei Web-UI-Entwicklung, Flask-Routes, WebSocket, Frontend-Änderungen, oder wenn "webserver", "Flask", "WebSocket", "ankersrv.js" erwähnt wird.
version: 1.0.0
---

# Web Development Skill

## Flask Backend

- Entry: `web/__init__.py`
- Config: `web/config.py`
- Default Port: 4470

## Services

| Service | Datei | Funktion |
|---------|-------|----------|
| MQTT | web/service/mqtt.py | Event-Streaming |
| PPPP | web/service/pppp.py | LAN-Connection |
| Video | web/service/video.py | Camera Stream |
| FileTransfer | web/service/filetransfer.py | Upload/Print |

## WebSocket Endpoints

- `/ws/mqtt` - MQTT Events
- `/ws/pppp-state` - Connection State
- `/ws/video` - Video Stream
- `/ws/ctrl` - Control Commands

## Frontend

| Datei | Funktion |
|-------|----------|
| static/ankersrv.js | Main JS (Cash.js) |
| static/ankersrv.css | Styling |
| static/tabs/ | HTML Templates |
| static/vendor/ | Bootstrap, JMuxer |
| static/libflagship.js | [GENERATED] Protocol JS |

## Service Pattern

```python
class MyService(Service):
    def worker_init(self):
        # Setup
        pass

    def worker_run(self):
        # Main loop
        pass

    def worker_stop(self):
        # Cleanup
        pass
```

## Starting the Web Server

```bash
# Default (localhost:4470)
./ankerctl.py webserver run

# Custom host/port
./ankerctl.py webserver run --host 0.0.0.0 --port 8080

# Via Docker
docker compose up
```

## Frontend Guidelines

- Use Cash.js (lightweight jQuery alternative) for DOM manipulation
- Avoid introducing new frameworks
- Follow existing style in `static/ankersrv.js`
