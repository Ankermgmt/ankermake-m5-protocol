# Security Audit & Bug Report — ankerctl

**Datum:** 2026-02-17
**Geprüfter Commit:** aktueller `main`-Branch

---

## Zusammenfassung

Dieses Dokument beschreibt Sicherheitslücken und Fehler im `ankermake-m5-protocol`-Repository. Die Findings sind unterteilt in **behebbare Probleme** und **Protokoll-bedingte Limitierungen** (durch das Anker-Druckerprotokoll vorgegeben, nicht änderbar).

| Kategorie | Schweregrad | Anzahl |
|-----------|-------------|--------|
| Behebbar  | KRITISCH    | 2      |
| Behebbar  | HOCH        | 2      |
| Behebbar  | MITTEL      | 5      |
| Behebbar  | NIEDRIG     | 1      |
| Protokoll-bedingt | INFO | 4      |

---

## Behebbare Probleme

### KRITISCH

#### K1 — Web-Server ohne Authentifizierung

**Datei:** `web/__init__.py`

Der Flask-Webserver bietet keinerlei Authentifizierung. Alle Endpunkte – Druckersteuerung, Datei-Upload, GCode-Ausführung, Konfigurationsänderungen – sind für jeden im Netzwerk zugänglich. Wird der Server nicht auf `127.0.0.1` gebunden, kann jeder im LAN den Drucker steuern.

**Betroffene Endpunkte:**

| Endpunkt | Risiko |
|----------|--------|
| `POST /api/files/local` | Beliebige Dateien an Drucker senden |
| `POST /api/printer/gcode` | Beliebigen GCode ausführen |
| `POST /api/printer/control` | Drucker steuern (Start/Stop/Pause) |
| `POST /api/ankerctl/config/login` | Anmeldedaten abfangen |
| `POST /api/ankerctl/config/upload` | Konfiguration überschreiben |
| `GET /api/ankerctl/server/reload` | Server-Neustart auslösen |

**Empfehlung:** Ein einfaches, **optionales Passwort** implementieren, das als API-Key fungiert. Slicer (PrusaSlicer, OrcaSlicer) unterstützen den `X-Api-Key`-Header im OctoPrint-Protokoll.

**Umsetzung:**
- Passwort in Config speichern (`api_password` in `default.json`)
- Kein Passwort gesetzt → Server bleibt offen (Abwärtskompatibilität)
- Passwort gesetzt → alle API-Endpunkte prüfen `X-Api-Key`-Header
- Web-UI: Session-Cookie nach einmaliger Passwort-Eingabe
- Slicer: Passwort als `X-Api-Key`-Header (OctoPrint-kompatibel)
- **CSRF wird dadurch ebenfalls entschärft** (Browser senden Custom-Header nicht automatisch bei Cross-Site-Requests)
- Zusätzlich `SameSite=Strict` auf Session-Cookies setzen

---

#### K2 — Konfiguration ohne Dateischutz gespeichert

**Datei:** `cli/config.py`, Zeilen 78–82

Auth-Token, MQTT-Schlüssel und P2P-Keys werden in `~/.config/ankerctl/default.json` gespeichert. Das Verzeichnis hat keine eingeschränkten Berechtigungen.

**Gespeicherte Geheimnisse:**
- `auth_token` (Anker-Cloud-API-Zugang)
- `mqtt_key` (AES-Schlüssel für MQTT)
- `p2p_key` (DSK-Schlüssel für P2P)

**Empfehlung:** Config-Verzeichnis bei Erstellung mit `0700` absichern. Hashing ist **nicht anwendbar**, da die Schlüssel im Klartext für die Druckerkommunikation benötigt werden.

```python
dirs.user_config_path.mkdir(exist_ok=True, parents=True)
os.chmod(dirs.user_config_path, 0o700)
```

---

### HOCH

#### H1 — Unsichere Zufallszahlen für Sicherheitscodes

**Datei:** `libflagship/seccode.py`, Zeile 58

```python
import random  # NICHT kryptographisch sicher!

def gen_rand_seed(mac):
    rnd = random.randint(10000000, 99999999)
```

`random.randint()` nutzt den Mersenne-Twister-PRNG, der vorhersagbar ist.

**Empfehlung:** `secrets.randbelow(90000000) + 10000000` verwenden.

---

#### H2 — WebSocket-Eingaben ohne Validierung

**Datei:** `web/__init__.py`, Zeilen 195–234

Der `/ws/ctrl`-Endpunkt leitet JSON-Werte direkt an Geräte-APIs weiter, ohne Typ- oder Wertebereichsprüfung:

```python
msg = json.loads(sock.receive())
if "light" in msg:
    vq.api_light_state(msg["light"])  # Keine Prüfung
if "quality" in msg:
    vq.api_video_mode(msg["quality"])  # Keine Prüfung
```

**Empfehlung:** Eingabewerte auf erwartete Typen und Wertebereiche prüfen.

---

### MITTEL

#### M1 — Docker-Container läuft als root

**Datei:** `Dockerfile`

Kein `USER`-Befehl → Container läuft als `root`.

**Empfehlung:**
```dockerfile
RUN useradd -m ankerctl
USER ankerctl
```

---

#### M2 — Fehlermeldungen leaken interne Details

**Datei:** `web/__init__.py`, Zeilen 340, 344, 444

Interne Exception-Informationen werden an HTTP-Clients weitergegeben:

```python
f"Exception information: {E}"           # Zeile 444
f"Unexpected Error occurred: {err}"      # Zeile 344
```

**Empfehlung:** Benutzerfreundliche Fehlermeldungen anzeigen, Details nur in Server-Logs.

---

#### M3 — MQTT-Checksummen-Fehler wird ignoriert

**Datei:** `libflagship/megajank.py`, Zeilen 35–39

```python
def mqtt_checksum_remove(payload):
    if xor_bytes(payload) != 0:
        # raise ...           ← Auskommentiert!
        print(f"MALFORMED MESSAGE: {payload}")
    return payload[:-1]       # Nachricht wird trotzdem verarbeitet
```

**Empfehlung:** Exception aktivieren, fehlerhafte Nachrichten verwerfen.

---

#### M4 — Fehlende Größenlimitierung beim Datei-Upload

**Datei:** `web/service/filetransfer.py`, Zeile 36

```python
data = fd.read()  # Gesamte Datei in den Speicher – kein Limit
```

**Empfehlung:** `app.config['MAX_CONTENT_LENGTH']` setzen (z.B. 500 MB).

---

#### M5 — Mutable Default-Argument

**Datei:** `libflagship/httpapi.py`, Zeile 116

```python
def equipment_get_dsk_keys(self, station_sns, invalid_dsks={}):
#                                              ^^^^^^^^^^^^^^ Bug!
```

**Empfehlung:** `invalid_dsks=None` verwenden, im Body `if invalid_dsks is None: invalid_dsks = {}`.

---

### NIEDRIG

#### N1 — Duplizierter Code bei Dateisuche

**Datei:** `ankerctl.py`, Zeilen 373–398 und 416–441

Die File-Detection-Logik für `config decode` und `config import` ist nahezu identisch dupliziert.

**Empfehlung:** Gemeinsame Hilfsfunktion extrahieren (`_find_login_json()`).

---

## Protokoll-bedingte Limitierungen (nicht behebbar)

Die folgenden Findings sind durch das Anker-Druckerprotokoll vorgegeben. Sie sind hier zur Dokumentation aufgeführt, können aber nicht geändert werden, ohne die Kompatibilität mit dem Drucker zu brechen.

### P1 — Hardcodierter AES-IV für MQTT-Verschlüsselung

**Datei:** `libflagship/megajank.py`, Zeilen 25–30

Statischer IV `b"3DPrintAnkerMake"` bei AES-CBC. Wird vom Protokoll vorgeschrieben und zur MQTT-Verschlüsselung benötigt.

### P2 — Hardcodierter AES-Schlüssel in logincache.py

**Datei:** `libflagship/logincache.py`, Zeile 5

Fester Schlüssel `1b55f97793d58864571e1055838cac97` mit AES-ECB für die Entschlüsselung der Login-Cache-Daten der AnkerMake-Slicer-Software. Durch die Slicer-Software vorgegeben.

### P3 — `Gtoken`-Header mit MD5-Hash

**Datei:** `libflagship/httpapi.py`, Zeilen 85, 95

MD5-Hash der `user_id` als Auth-Token im HTTP-Header. Durch das Anker-Cloud-API vorgegeben.

### P4 — network_mode: host im Docker Compose

**Datei:** `docker-compose.yaml`, Zeile 10

Voller Host-Netzwerkzugriff. Für das asymmetrische PPPP-UDP-Protokoll technisch erforderlich.

---

## Zusammenfassung der behebbaren Maßnahmen

| # | Maßnahme | Schweregrad | Aufwand |
|---|----------|-------------|---------|
| 1 | Optionales Passwort als API-Key (Slicer-kompatibel via `X-Api-Key`) + `SameSite`-Cookies | KRITISCH | Mittel |
| 2 | Config-Verzeichnis mit `0700` absichern | KRITISCH | Gering |
| 3 | `random` → `secrets` in `seccode.py` | HOCH | Gering |
| 4 | WebSocket-Eingabevalidierung | HOCH | Gering |
| 5 | Docker: non-root User | MITTEL | Gering |
| 6 | Fehlermeldungen bereinigen | MITTEL | Gering |
| 7 | MQTT-Checksum-Fehler nicht ignorieren | MITTEL | Gering |
| 8 | Upload-Größenlimit | MITTEL | Gering |
| 9 | Mutable Default-Argument fixen | MITTEL | Gering |
| 10 | Duplizierte File-Detection refactoren | NIEDRIG | Gering |
