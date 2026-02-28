# ankerctl (Docker) – Fortschritt / Notes

Ziel: Web-UI (PPPP Status + Video) stabil bekommen und Fixes **persistent** machen.

## Deploy/Setup (Host)

- Compose: Arcane-Projekt `3D-Printing` → `/app/data/projects/3D-Printing/compose.yaml` (im arcane-Container)
- Service: `ankerctl`
- Image: `django01982/ankerctl:local` (lokaler Build aus diesem Repo)
- Build-Context: `/data_hdd/ankermake-m5-protocol-django1982`
- Web-UI: `http://192.168.1.24:4470/` (host networking)
- Persistente Config: `/apps/docker/ankerctl` → im Container `/home/ankerctl/.config/ankerctl`
- Env-Datei: `/apps/docker/docker-mgmt/arcane/projects/3D-Printing/.env`
- Legacy Overlay-Dockerfile (nur Archiv): `/apps/docker/ankerctl/docs/ankerctl-overlay.Dockerfile`

### Image neu bauen (ohne Arcane)

```bash
sudo docker build -t django01982/ankerctl:local /data_hdd/ankermake-m5-protocol-django1982
```

### Container neu starten (ohne Arcane, manuell)

```bash
sudo docker stop ankerctl && sudo docker rm ankerctl
sudo docker run -d \
  --name ankerctl \
  --user 1000:1000 \
  --network host \
  --restart unless-stopped \
  -e FLASK_HOST=192.168.1.24 \
  -e FLASK_PORT=4470 \
  -e FLASK_SECRET_KEY=<KEY_AUS_ENV> \
  -e ANKERCTL_API_KEY=<KEY_AUS_ENV> \
  -v /apps/docker/ankerctl:/home/ankerctl/.config/ankerctl \
  -v /apps/docker/ankerctl/captures:/captures \
  django01982/ankerctl:local
```

### Logs

```bash
docker logs -f ankerctl
```

### Erstes Login nach Neustart (API-Key gesetzt)

Da der API-Key Browser-Sessions schützt, muss nach jedem Neustart **einmalig** die
URL mit `?apikey=` aufgerufen werden – das setzt den Session-Cookie:

```
http://192.168.1.24:4470/?apikey=<ANKERCTL_API_KEY>
```

Danach funktioniert die UI normal ohne weiteren Key in der URL.

---

## Bekannte Fallstricke

| Problem | Ursache | Fix |
|---------|---------|-----|
| "Unauthorized" beim Speichern | `FLASK_SECRET_KEY` nicht gesetzt → neuer Key bei jedem Start → Session ungültig | `FLASK_SECRET_KEY` in `.env` eintragen |
| HA MQTT `rc=5` (connection refused) | MQTT-Passwort leer, Broker verlangt Auth | Passwort in UI unter Setup → MQTT setzen |
| History zeigt nur "Loading..." | Cash.js kann Bootstrap-Events (`shown.bs.tab`) nicht korrekt abonnieren | Behoben: natives `addEventListener` statt `$.on()` |
| Timelapse speichern: 500 Error | `web.__init__._deep_update()` statt `_deep_update()` | Behoben: Copy-Paste-Fehler in `web/__init__.py:596` |
| MqttQueue startet nicht | `AnkerConfigManager` hat kein `.timelapse`-Attribut | Behoben: `TimelapseService` und `HomeAssistantService` nutzen jetzt `.open()` |

---

## Bisher persistent gepatcht (Overlay Image, historisch)

Hinweis: Diese Liste stammt aus dem Overlay-Image und dient nur als Referenz.
Die Fixes werden jetzt direkt im Repo gepflegt.

1. `Service.tap()` Race Fix – `web/lib/service.py`
2. PPPP UDP Timeout-Leak Fix + non-blocking Robustheit – `libflagship/ppppapi.py`
3. Browser/Websocket URL Fix – `static/ankersrv.js`
4. PPPP-State WS Handler stabiler – `web/__init__.py`
5. Video Frame Forwarding (XZYH → VideoQueue) – `web/service/pppp.py`, `web/service/video.py`
6. UI Fixes (SD/HD + Reconnect) – `static/ankersrv.js`
7. PPPPService: Single-Reader – `web/service/pppp.py`
8. Filetransfer: EOF/OSError als ConnectionError – `web/service/filetransfer.py`
9. PPPP AABB Reply Reader: Locking / Thread-Safety – `libflagship/ppppapi.py`
10. Test-Transfer: Metadata + Start/No-Act – `test_transfer.py`
11. Web: Upload-only Support + bessere Fehlermeldung – `web/__init__.py`, `web/util.py`, `web/service/filetransfer.py`

---

## Repo-Status (aktuell)

- Fixes aus 1, 2, 3, 4, 5, 6, 8, 9, 11 sind im Repo umgesetzt.
- Fix 7 (Single-Reader) ist im Repo nicht 1:1 relevant (Async-API).
- Fix 10 ist im Repo nicht vorhanden (kein `test_transfer.py`).

---

## Aktueller Status

- MQTT-Verbindung zum Drucker: ✅ stabil
- HA MQTT Discovery: ✅ verbindet (Passwort in UI eintragen)
- History-Tab: ✅ lädt korrekt
- Timelapse-Einstellungen speichern: ✅ funktioniert
- API-Key / Session: ✅ persistent (FLASK_SECRET_KEY in .env)
- Video-Stabilität: noch nicht unter Last verifiziert

## Fork/Repo

Arbeits-Repo (Fork): `/data_hdd/ankermake-m5-protocol-django1982`
Remote: `git@github.com:django1982/ankermake-m5-protocol`
