# Umsetzungsplan — Security Fixes für ankerctl

Basierend auf dem [Security Audit](./SECURITY_AUDIT.md). Alle Phasen umgesetzt.

---

## Phase 1 — Quick Wins ✅

| # | Maßnahme | Datei | Änderung |
|---|----------|-------|----------|
| 1.1 | Config-Verzeichnis `0700` (K2) | `cli/config.py` | `os.chmod(dirs.user_config_path, 0o700)` nach `mkdir()` |
| 1.2 | `secrets` statt `random` (H1) | `libflagship/seccode.py` | `secrets.randbelow(90000000) + 10000000` |
| 1.3 | Mutable Default fixen (M5) | `libflagship/httpapi.py` | `invalid_dsks=None` + Body-Initialisierung |
| 1.4 | Upload-Limit (M4) | `web/__init__.py` | `UPLOAD_MAX_MB` ENV (Default: 2 GB) |

---

## Phase 2 — Kleine Fixes ✅

| # | Maßnahme | Datei | Änderung |
|---|----------|-------|----------|
| 2.1 | MQTT-Checksum (M3) | `libflagship/megajank.py` | `raise ValueError` statt `print` + Fallthrough |
| 2.2 | Fehlermeldungen (M2) | `web/__init__.py` | Generische UI-Meldungen, `log.exception()` serverseitig |
| 2.3 | WebSocket-Validierung (H2) | `web/__init__.py` | `isinstance()`-Prüfung für `light`, `quality`, `video_profile`, `video_enabled` |
| 2.4 | Docker non-root (M1) | `Dockerfile`, `docker-compose.yaml` | User `ankerctl`, UID/GID konfigurierbar, Volume-Pfad angepasst |
| 2.5 | Code-Duplikation (N1) | `ankerctl.py` | `_find_login_file()` extrahiert |

---

## Phase 3 — API-Key Authentifizierung ✅

Optionaler API-Key für den Webserver. Kein Key = kein Auth (abwärtskompatibel).

### 3.1 — API-Key Speicherung

**Datei:** `cli/config.py`

API-Key wird als separate Config-Datei `api_key.json` gespeichert (unabhängig von `default.json`):

```python
config.get_api_key()       # → str | None
config.set_api_key(key)    # → speichert in api_key.json
config.remove_api_key()    # → löscht api_key.json
```

**Precedence:** `ANKERCTL_API_KEY` ENV → Config-Datei → kein Auth

### 3.2 — CLI-Befehle

**Datei:** `ankerctl.py`

```bash
./ankerctl.py config set-password              # Generiert Key mit secrets.token_hex(16)
./ankerctl.py config set-password MEIN_KEY      # Eigener Key
./ankerctl.py config remove-password            # Löscht Key, Auth deaktiviert
```

### 3.3 — Flask-Middleware

**Datei:** `web/__init__.py`

`@app.before_request`-Handler mit folgender Prüfkette:

```
Kein API-Key konfiguriert?  →  Zugriff erlaubt
  ↓
/static/* Request?           →  Zugriff erlaubt (Assets brauchen kein Auth)
  ↓
X-Api-Key Header korrekt?   →  Zugriff erlaubt (Slicer)
  ↓
?apikey= URL-Parameter?     →  Session-Cookie setzen, Redirect auf saubere URL
  ↓
Session-Cookie gültig?      →  Zugriff erlaubt (Browser)
  ↓
                              →  401 Unauthorized (JSON)
```

### 3.5 — Cookie-Sicherheit

```python
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'   # CSRF-Schutz
app.config['SESSION_COOKIE_HTTPONLY'] = True         # XSS-Schutz
```

### Docker-Nutzung

API-Key per Environment-Variable in `docker-compose.yaml`:

```yaml
environment:
    - ANKERCTL_API_KEY=mein-geheimer-key
```

---

## Übersicht

| Phase | Maßnahmen | Status |
|-------|-----------|--------|
| 1 | Config `0700`, `secrets`, Mutable Default, Upload-Limit | ✅ |
| 2 | MQTT-Checksum, Fehlermeldungen, WebSocket-Validierung, Docker non-root, Dedup | ✅ |
| 3 | API-Key Auth, CLI, Middleware, SameSite-Cookie, Docker ENV | ✅ |
