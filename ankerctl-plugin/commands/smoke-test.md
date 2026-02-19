---
description: Führt Smoke-Tests für MQTT und PPPP aus
argument-hint: [mqtt|pppp|all]
allowed-tools: [Bash, Read]
---

# Smoke Test Command

Führt schnelle Validierungstests aus.

## Argumente

$ARGUMENTS

- `mqtt`: Nur MQTT-Konnektivität testen
- `pppp`: Nur PPPP/LAN-Suche testen
- `all` oder leer: Beide Tests ausführen

## Tests

1. **MQTT**: `./ankerctl.py mqtt monitor` (5 Sekunden)
2. **PPPP**: `./ankerctl.py pppp lan-search`

## Voraussetzungen

- Gültige Konfiguration in ~/.config/ankerctl/
- Netzwerkverbindung zum Drucker

## Befehle

```bash
# MQTT connectivity test
timeout 5 ./ankerctl.py mqtt monitor || true

# PPPP/LAN search
./ankerctl.py pppp lan-search

# Both tests
timeout 5 ./ankerctl.py mqtt monitor || true && ./ankerctl.py pppp lan-search
```
