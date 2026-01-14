# ankerctl (Docker) – Fortschritt / Notes

Ziel: Web-UI (PPPP Status + Video) stabil bekommen und Fixes **persistent** machen.

## Deploy/Setup (Host)

- Compose: `/apps/docker/docker-mgmt/arcane/projects/HomeAssistant/compose.yaml`
- Service: `ankerctl`
- Image: `ankerctl-local:patched` (lokaler Overlay-Build)
- Build-Context (Ziel): `/data_hdd/ankermake-m5-protocol-django1982`
- Web-UI: `http://192.168.1.24:4470/` (host networking)
- Persistente Config: `/apps/docker/ankerctl` → im Container `/root/.config/ankerctl`
- Legacy Overlay-Dockerfile (nur Archiv): `/apps/docker/ankerctl/docs/ankerctl-overlay.Dockerfile`

Rebuild/Restart nur für `ankerctl`:

```bash
docker compose -f /apps/docker/docker-mgmt/arcane/projects/HomeAssistant/compose.yaml up -d --build ankerctl
```

Logs:

```bash
docker logs -f ankerctl
```

## Bisher persistent gepatcht (Overlay Image, historisch)

Hinweis: Diese Liste stammt aus dem Overlay-Image und dient nur als Referenz.
Die Fixes werden jetzt direkt im Repo gepflegt.

1) `Service.tap()` Race Fix
- Datei im Image: `/app/web/lib/service.py`
- `self.handlers.remove(handler)` wird jetzt im `finally` gegen `ValueError` abgesichert.

2) PPPP UDP Timeout-Leak Fix + non-blocking Robustheit
- Datei im Image: `/app/libflagship/ppppapi.py`
- `recv()` speichert/restauriert Socket-Timeout (sonst „leakt“ Timeout in `sendto()` Pfade).
- `BlockingIOError` (non-blocking recv) wird wie ein Timeout behandelt.

3) Browser/Websocket URL Fix
- Datei im Image: `/app/static/ankersrv.js`
- WS-URLs für `/ws/video` + `/ws/ctrl` waren kaputt (fehlendes `//`).

4) PPPP-State WS Handler stabiler
- Datei im Image: `/app/web/__init__.py`
- `/ws/pppp-state` nutzt jetzt kein `ServiceManager.stream(timeout=...)` mehr (das endete auf `Empty`).
- Stattdessen: startet PPPP non-blocking via `app.svc.get("pppp", ready=False)` und sendet `{"status":"connected"}` + Keepalive.

5) Video Frame Forwarding (XZYH → VideoQueue)
- Dateien im Image:
  - `/app/web/service/pppp.py` (xzyh drain + `xzyh_handlers`)
  - `/app/web/service/video.py` (registriert auf `pppp.xzyh_handlers`)
- Ergebnis: `/ws/video` kann binary Frames liefern (war zwischenzeitlich bestätigt).

6) UI Fixes (SD/HD + Reconnect)
- Datei im Image: `/app/static/ankersrv.js`
- SD/HD Buttons: Active-State korrekt (keine `.siblings()`-Falle mehr).
- Video/PPPP Websockets: Reconnect wieder aktiv; Video-Reconnect ist an/aus an den “Enable Video” Toggle gekoppelt.

7) PPPPService: Single-Reader + kein “Running ohne API”
- Datei im Image: `/app/web/service/pppp.py`
- `worker_run()` liest nicht mehr parallel vom UDP-Socket (nur der API-Thread liest vom Socket).
- `worker_start()` kann nicht mehr „erfolgreich“ zurückkehren, solange kein API/Connect steht (verhindert `No pppp connection to printer` bei Print-Upload).

8) Filetransfer: EOF/OSError als ConnectionError
- Datei im Image: `/app/web/service/filetransfer.py`
- EOF/OSError während Upload wird als `ConnectionError("PPPP transfer failed")` gemeldet (kein HTTP 500 mehr).

9) PPPP AABB Reply Reader: Locking / Thread-Safety
- Datei im Image: `/app/libflagship/ppppapi.py`
- `AnkerPPPPApi.recv_aabb()` nutzt jetzt `with fd.lock:` (vorher ohne Lock → parallele `Pipe.recv()` Calls zwischen Video-Drain und File-Transfer → `EOFError: Ran out of input` + PPPP-Service crash).

10) Test-Transfer: Metadata + Start/No-Act
- Datei im Image: `/app/test_transfer.py`
- Fix: kein doppeltes `\\x00` mehr an der Metadata (`FileUploadInfo.__bytes__` hängt schon `\\x00` an).
- `send_file(..., start_print=True)` → bei `start_print=False` wird **kein** `FileTransfer.END` gesendet (Upload-only).

11) Web: Upload-only Support + bessere Fehlermeldung
- Dateien im Image:
  - `/app/web/__init__.py` (`/api/files/local` akzeptiert jetzt `print=false`)
  - `/app/web/util.py` (`upload_file_to_printer(..., start_print=...)`)
  - `/app/web/service/filetransfer.py` (`start_print` durchreichen; `PPPPError`/EOF/OSError → ConnectionError inkl. Grund)

## Repo-Status (aktuell)

- Fixes aus 1, 2, 4, 5, 8, 9, 11 sind im Repo umgesetzt.
- Fix 3 (WS-URLs) und SD/HD Active-State wurden ins Repo portiert.
- Fix 7 (Single-Reader) ist im Repo nicht 1:1 relevant (Async-API); bitte nach Live-Tests bewerten.
- Fix 10 ist im Repo nicht vorhanden (kein `test_transfer.py`).

## Aktueller Status / Probleme

- Video-Stabilität muss noch real unter Last verifiziert werden (start/stop, längere Laufzeit).
- Print-Upload via Web-UI sollte jetzt nicht mehr sofort mit `No pppp connection to printer` abbrechen; bitte live testen.

## Nächster Fix-Verdacht (Root Cause)

Sehr wahrscheinlich liest `PPPPService` **parallel** zum `AnkerPPPPApi`-Thread vom gleichen UDP-Socket:
- `AnkerPPPPApi.start()` startet eigenen recv/process-loop
- `PPPPService.worker_run()` ruft zusätzlich `self._api.recv()` + `process()` auf

Das ist ein klassischer „two readers one socket“ Bug → Paketverlust/Out-of-order → Video/Commands unzuverlässig.

Plan: PPPPService so umbauen, dass **nur ein** Reader aktiv ist (API-Thread oder Service – aber nicht beides).

Status: Patch ist im Overlay aktiv (`patch_pppp_service_single_reader` + `patch_pppp_service_worker_run/worker_start`).

## Fork/Repo

Arbeits-Repo (Fork): `/data_hdd/ankermake-m5-protocol-django1982`
Wenn alles stabil läuft: Patches sauber ins Repo übertragen, committen und pushen:
`git@github.com:django1982/ankermake-m5-protocol`
