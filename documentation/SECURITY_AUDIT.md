# Security Audit — ankerctl

**Datum:** 2026-02-17
**Geprüfter Commit:** aktueller `master`-Branch

---

## Zusammenfassung

Dieses Dokument beschreibt Sicherheitslücken und Fehler im `ankermake-m5-protocol`-Repository. Die Findings sind unterteilt in **behebbare Probleme** und **Protokoll-bedingte Limitierungen** (durch das Anker-Druckerprotokoll vorgegeben, nicht änderbar).

| Kategorie | Schweregrad | Gefunden | Behoben |
|-----------|-------------|----------|---------|
| Behebbar  | KRITISCH    | 2        | ✅ 2    |
| Behebbar  | HOCH        | 2        | ✅ 2    |
| Behebbar  | MITTEL      | 5        | ✅ 5    |
| Behebbar  | NIEDRIG     | 1        | ✅ 1    |
| Protokoll-bedingt | INFO | 4        | —       |

> **Alle behebbaren Findings sind umgesetzt.** Details siehe [Umsetzungsplan](./SECURITY_IMPLEMENTATION_PLAN.md).

---

## Behebbare Probleme

### KRITISCH

#### K1 — Web-Server ohne Authentifizierung ✅

**Datei:** `web/__init__.py`
**Status:** Behoben (Phase 3)

Der Flask-Webserver bot keinerlei Authentifizierung. Alle Endpunkte – Druckersteuerung, Datei-Upload, GCode-Ausführung, Konfigurationsänderungen – waren für jeden im Netzwerk zugänglich.

**Betroffene Endpunkte:**

| Endpunkt | Risiko |
|----------|--------|
| `POST /api/files/local` | Beliebige Dateien an Drucker senden |
| `POST /api/printer/gcode` | Beliebigen GCode ausführen |
| `POST /api/printer/control` | Drucker steuern (Start/Stop/Pause) |
| `POST /api/ankerctl/config/login` | Anmeldedaten abfangen |
| `POST /api/ankerctl/config/upload` | Konfiguration überschreiben |
| `GET /api/ankerctl/server/reload` | Server-Neustart auslösen |

**Umsetzung:**
- Optionaler API-Key (`config set-password` / `ANKERCTL_API_KEY` ENV)
- Kein Key → offen (Abwärtskompatibilität)
- Key gesetzt → `X-Api-Key` Header (Slicer), `?apikey=` URL-Parameter (Browser/Session), Session-Cookie
- `SameSite=Strict` + `HttpOnly` auf Session-Cookies (CSRF-Schutz)

---

#### K2 — Konfiguration ohne Dateischutz gespeichert ✅

**Datei:** `cli/config.py`
**Status:** Behoben (Phase 1)

Auth-Token, MQTT-Schlüssel und P2P-Keys werden in `~/.config/ankerctl/default.json` gespeichert. Das Verzeichnis hatte keine eingeschränkten Berechtigungen.

**Umsetzung:** Config-Verzeichnis wird mit `os.chmod(path, 0o700)` abgesichert.

---

### HOCH

#### H1 — Unsichere Zufallszahlen für Sicherheitscodes ✅

**Datei:** `libflagship/seccode.py`
**Status:** Behoben (Phase 1)

`random.randint()` (Mersenne-Twister, vorhersagbar) → `secrets.randbelow()` (kryptographisch sicher).

---

#### H2 — WebSocket-Eingaben ohne Validierung ✅

**Datei:** `web/__init__.py`, `/ws/ctrl`-Handler
**Status:** Behoben (Phase 2)

JSON-Werte wurden direkt an Geräte-APIs weitergeleitet. Jetzt `isinstance()`-Prüfungen für `light` (bool), `quality`/`video_profile` (int), `video_enabled` (bool).

---

### MITTEL

#### M1 — Docker-Container läuft als root ✅

**Datei:** `Dockerfile`, `docker-compose.yaml`
**Status:** Behoben (Phase 2)

Container läuft als non-root User `ankerctl` mit konfigurierbarer UID/GID.

---

#### M2 — Fehlermeldungen leaken interne Details ✅

**Datei:** `web/__init__.py`
**Status:** Behoben (Phase 2)

Benutzerfreundliche Fehlermeldungen, Details nur in Server-Logs via `log.exception()`.

---

#### M3 — MQTT-Checksummen-Fehler wird ignoriert ✅

**Datei:** `libflagship/megajank.py`
**Status:** Behoben (Phase 2)

`print()` + Fallthrough → `raise ValueError()`.

---

#### M4 — Fehlende Größenlimitierung beim Datei-Upload ✅

**Datei:** `web/__init__.py`
**Status:** Behoben (Phase 1)

Konfigurierbares Limit via `UPLOAD_MAX_MB` ENV (Default: 2 GB).

---

#### M5 — Mutable Default-Argument ✅

**Datei:** `libflagship/httpapi.py`
**Status:** Behoben (Phase 1)

`invalid_dsks={}` → `invalid_dsks=None` mit Initialisierung im Body.

---

### NIEDRIG

#### N1 — Duplizierter Code bei Dateisuche ✅

**Datei:** `ankerctl.py`
**Status:** Behoben (Phase 2)

Login-JSON-Autodetect in `_find_login_file()` extrahiert.

---

## Protokoll-bedingte Limitierungen (nicht behebbar)

Die folgenden Findings sind durch das Anker-Druckerprotokoll vorgegeben. Sie können nicht geändert werden, ohne die Kompatibilität mit dem Drucker zu brechen.

| # | Finding | Datei | Begründung |
|---|---------|-------|------------|
| P1 | Hardcodierter AES-IV `3DPrintAnkerMake` | `libflagship/megajank.py` | MQTT-Protokoll des Druckers |
| P2 | Hardcodierter AES-Schlüssel (ECB) | `libflagship/logincache.py` | AnkerMake-Slicer-Format |
| P3 | MD5-basierter `Gtoken`-Header | `libflagship/httpapi.py` | Anker-Cloud-API |
| P4 | `network_mode: host` in Docker | `docker-compose.yaml` | PPPP-UDP-Protokoll |
