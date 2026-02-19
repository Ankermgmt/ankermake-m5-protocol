---
name: protocol-dev
description: Aktiviere bei Protokoll-Änderungen, MQTT/PPPP-Entwicklung, .stf-Dateien, Transwarp-Templates, oder wenn "Protokoll", "MQTT", "PPPP", "specification" erwähnt wird.
version: 1.0.0
---

# Protocol Development Skill

## Architektur

- **MQTT**: Verschlüsselt (AES-256-CBC), topic-basiertes Messaging mit Anker Cloud
- **PPPP**: Asymmetrisches UDP P2P-Protokoll für LAN-Kommunikation

## Wichtige Dateien

| Datei | Zweck |
|-------|-------|
| specification/mqtt.stf | MQTT-Protokoll-Definition |
| specification/pppp.stf | PPPP-Protokoll-Definition |
| templates/python/*.tpl | Python-Code-Templates |
| templates/js/*.tpl | JavaScript-Code-Templates |

## Generierte Dateien (NICHT manuell bearbeiten!)

- `libflagship/mqtt.py`
- `libflagship/pppp.py`
- `libflagship/amtypes.py`
- `static/libflagship.js`

## Workflow für Protokolländerungen

1. Bearbeite `specification/*.stf`
2. Optional: Bearbeite `templates/`
3. `make diff` - Preview der Änderungen
4. `make update` - Code generieren
5. Testen mit CLI und Web UI

## MQTT Topics

- **To Printer:** `/device/maker/{SN}/command`, `/device/maker/{SN}/query`
- **From Printer:** `/phone/maker/{SN}/notice`, `/phone/maker/{SN}/command/reply`

## MQTT Command Pattern

```python
client = cli.mqtt.mqtt_open(env.config, env.printer_index, env.insecure)
cmd = {
    "commandType": MqttMsgType.ZZ_MQTT_CMD_XXX.value,
    "cmdData": "...",
    "cmdLen": len("..."),
}
client.command(cmd)
response = client.await_response(MqttMsgType.ZZ_MQTT_CMD_XXX)
```

## PPPP File Transfer Pattern

```python
api = cli.pppp.pppp_open(env.config, env.printer_index, dumpfile=env.pppp_dump)
fui = FileUploadInfo.from_data(data, filename, user_name="ankerctl", ...)
cli.pppp.pppp_send_file(api, fui, data, rate_limit_mbps=rate_limit_mbps)
api.aabb_request(b"", frametype=FileTransfer.END)  # Start print
api.stop()
```

## Common MQTT Commands

| Command | Hex | Description |
|---------|-----|-------------|
| `ZZ_MQTT_CMD_GCODE_COMMAND` | 0x0413 | Send raw GCode |
| `ZZ_MQTT_CMD_NOZZLE_TEMP` | 0x03eb | Set nozzle temp (value * 100) |
| `ZZ_MQTT_CMD_HOTBED_TEMP` | 0x03ec | Set bed temp (value * 100) |
| `ZZ_MQTT_CMD_PRINT_CONTROL` | 0x03f0 | Start/Pause/Stop print |
| `ZZ_MQTT_CMD_MOVE_ZERO` | 0x0402 | Home axes (G28) |
