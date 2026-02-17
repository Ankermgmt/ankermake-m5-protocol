# Umsetzungsplan — Security Fixes für ankerctl

Basierend auf dem [Security Audit](./SECURITY_AUDIT.md). Geordnet nach Priorität.

---

## Phase 1 — Quick Wins (Aufwand: je < 30 Min)

Minimale Codeänderungen, sofort umsetzbar.

### 1.1 Config-Verzeichnis absichern (K2)

**Datei:** `cli/config.py` → `BaseConfigManager.__init__`

`Path.mkdir(mode=...)` ändert nicht die Berechtigungen eines bereits existierenden Verzeichnisses. Daher expliziter `os.chmod()` nach dem `mkdir`:

```diff
  dirs.user_config_path.mkdir(exist_ok=True, parents=True)
+ import os
+ os.chmod(dirs.user_config_path, 0o700)
```

---

### 1.2 `random` → `secrets` (H1)

**Datei:** `libflagship/seccode.py`

```diff
- import random
+ import secrets

  def gen_rand_seed(mac):
-     rnd = random.randint(10000000, 99999999)
+     rnd = secrets.randbelow(90000000) + 10000000
```

> **Hinweis:** Das Ergebnis bleibt identisch (Wertebereich `[10000000, 99999999]`). Nur die Quelle der Zufallszahlen wird kryptographisch sicher. Keine Auswirkung auf Protokollkompatibilität.

---

### 1.3 Mutable Default-Argument fixen (M5)

**Datei:** `libflagship/httpapi.py`

```diff
- def equipment_get_dsk_keys(self, station_sns, invalid_dsks={}):
+ def equipment_get_dsk_keys(self, station_sns, invalid_dsks=None):
+     if invalid_dsks is None:
+         invalid_dsks = {}
```

---

### 1.4 Upload-Größenlimit (M4)

**Datei:** `web/__init__.py`

GCode-Dateien für komplexe Modelle können mehrere hundert MB groß werden. Ein zu niedriges Limit (z.B. 500 MB) könnte den Betrieb stören. Empfehlung: **konfigurierbares Limit** über Environment-Variable mit großzügigem Default als reine DoS-Absicherung.

```python
import os
max_upload_mb = int(os.getenv("UPLOAD_MAX_MB", "2048"))  # Default: 2 GB
app.config['MAX_CONTENT_LENGTH'] = max_upload_mb * 1024 * 1024
```

> Alternativ: Kein Limit setzen, wenn K1 (Authentifizierung) umgesetzt ist, da dann nur authentifizierte Benutzer hochladen können.

---

## Phase 2 — Kleine Fixes (Aufwand: je 1–2 Std)

### 2.1 MQTT-Checksum-Fehler behandeln (M3)

**Datei:** `libflagship/megajank.py`

```diff
  def mqtt_checksum_remove(payload):
      if xor_bytes(payload) != 0:
-         # raise ...
-         print(f"MALFORMED MESSAGE: {payload}")
-     return payload[:-1]
+         raise ValueError(f"MQTT checksum mismatch")
+     return payload[:-1]
```

---

### 2.2 Fehlermeldungen bereinigen (M2)

**Dateien:** `web/__init__.py`

Interne Exception-Details durch generische Meldungen ersetzen. `{err}` nur an `log.error()` weitergeben, nicht an die HTTP-Response.

---

### 2.3 WebSocket-Eingabevalidierung (H2)

**Datei:** `web/__init__.py`, `/ws/ctrl`-Handler

Prüfungen hinzufügen:
- `light`: boolescher Wert
- `quality`/`video_profile`: Integer aus definiertem Wertebereich
- `video_enabled`: boolescher Wert

---

### 2.4 Docker non-root User (M1)

**Datei:** `Dockerfile`

```diff
+ RUN useradd -m -s /bin/bash ankerctl
+ USER ankerctl
  ENTRYPOINT ["/app/ankerctl.py"]
```

---

### 2.5 Duplizierte File-Detection refactoren (N1)

**Datei:** `ankerctl.py`

Login-JSON-Autodetect in gemeinsame Funktion extrahieren, von `config_decode` und `config_import` aufrufen.

---

## Phase 3 — Optionales Passwort / API-Key (K1)

**Aufwand:** ca. 1 Tag

Das Kernfeature: Optionales Passwort, das als OctoPrint-kompatibler API-Key fungiert.

### 3.1 Config-Erweiterung

**Datei:** `cli/model.py`

Feld `api_password: Optional[str] = None` zum Config-Model hinzufügen.

### 3.2 CLI-Befehl zum Setzen/Entfernen

**Datei:** `ankerctl.py`

```
./ankerctl.py config set-password
./ankerctl.py config remove-password
```

### 3.3 Flask-Middleware für API-Key-Prüfung

**Datei:** `web/__init__.py`

`@app.before_request`-Handler:
1. Passwort aus Config laden
2. Kein Passwort gesetzt → Zugriff erlauben (Abwärtskompatibilität)
3. Passwort gesetzt:
   - `X-Api-Key`-Header prüfen (für Slicer)
   - Gültige Session prüfen (für Web-UI)
   - Sonst → 401 Unauthorized

### 3.4 Web-UI Login-Seite

**Datei:** `static/` (Template)

Einfache Passwort-Eingabe, die ein Session-Cookie setzt. Wird angezeigt, wenn Passwort konfiguriert ist und keine gültige Session besteht.

### 3.5 SameSite-Cookie

```python
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
app.config['SESSION_COOKIE_HTTPONLY'] = True
```

---

## Übersicht

| Phase | Maßnahme | Schweregrad | Aufwand |
|-------|----------|-------------|---------|
| 1.1 | Config-Verzeichnis `0700` | KRITISCH | ~5 Min |
| 1.2 | `secrets` statt `random` | HOCH | ~5 Min |
| 1.3 | Mutable Default fixen | MITTEL | ~5 Min |
| 1.4 | Upload-Limit | MITTEL | ~5 Min |
| 2.1 | MQTT-Checksum | MITTEL | ~30 Min |
| 2.2 | Fehlermeldungen | MITTEL | ~1 Std |
| 2.3 | WebSocket-Validierung | HOCH | ~1 Std |
| 2.4 | Docker non-root | MITTEL | ~30 Min |
| 2.5 | Code-Duplikation | NIEDRIG | ~30 Min |
| 3.x | Optionales Passwort (API-Key) | KRITISCH | ~1 Tag |
