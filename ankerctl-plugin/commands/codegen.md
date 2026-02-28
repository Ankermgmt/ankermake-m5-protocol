---
description: Generiert Protokoll-Code aus .stf Spezifikationen
argument-hint: [diff|update]
allowed-tools: [Bash, Read, Glob, Grep]
---

# Code Generation Command

Generiert Protokoll-Code aus specification/*.stf Dateien.

## Argumente

$ARGUMENTS

- `diff`: Zeigt Änderungen ohne zu schreiben (make diff)
- `update`: Regeneriert alle Dateien (make update)
- ohne Argument: Zeigt Status der generierten Dateien

## Workflow

1. Prüfe ob specification/*.stf oder templates/ geändert wurden
2. Führe entsprechenden make-Befehl aus
3. Zeige Zusammenfassung der Änderungen

## Generierte Dateien (NIEMALS manuell bearbeiten!)

- libflagship/mqtt.py
- libflagship/pppp.py
- libflagship/amtypes.py
- static/libflagship.js

## Befehle

```bash
# Preview changes
make diff

# Regenerate all files
make update

# Install transwarp tool (if needed)
make install-tools
```
