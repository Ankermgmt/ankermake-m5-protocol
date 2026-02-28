---
description: Startet ankerctl im Docker-Container
argument-hint: [--build]
allowed-tools: [Bash, Read]
---

# Docker Run Command

Startet den ankerctl Docker-Container.

## Argumente

$ARGUMENTS

- `--build`: Erzwingt Rebuild vor Start
- leer: Normaler Start

## Befehle

```bash
# Start container
docker compose up

# Start with rebuild
docker compose up --build

# Stop container
docker compose down
```

## WICHTIG

Docker erfordert `network_mode: host` wegen PPPP's asymmetrischem UDP.
Funktioniert NUR auf Linux-Hosts!

## Volume Mounts

- Configuration: `/home/ankerctl/.config/ankerctl` (maps to host config)
- SSL certificates: `/app/ssl`

## Multi-Architecture Support

CI builds for: `linux/arm/v7`, `linux/arm64`, `linux/amd64`
