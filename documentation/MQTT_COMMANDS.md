# AnkerMake M5 MQTT Protocol Documentation

This document describes the MQTT protocol used by AnkerMake M5 3D printers, based on reverse engineering of the `ankerctl` project.

## Connection Details

*   **Host:** `make-mqtt-eu.ankermake.com` (EU) or `make-mqtt.ankermake.com` (US)
*   **Port:** 8789
*   **Transport:** TLS
*   **Authentication:** Username and Password (retrieved from Anker HTTPS API)

## Topic Structure

*   **From Printer (Notice/Status):** `/phone/maker/{SN}/notice`
*   **From Printer (Replies):** `/phone/maker/{SN}/command/reply` and `/phone/maker/{SN}/query/reply`
*   **To Printer (Commands):** `/device/maker/{SN}/command`
*   **To Printer (Queries):** `/device/maker/{SN}/query`

## Message Format

Payloads are AES-encrypted.

*   **Encryption:** AES-256-CBC
*   **IV:** `b"3DPrintAnkerMake"` (Static)
*   **Key:** `mqtt_key` (Unique per printer, retrieved from Anker API)
*   **Padding:** PKCS7
*   **Structure:** A 64-byte binary header followed by the encrypted JSON payload and a 1-byte checksum (XOR).

## Command Types (MqttMsgType)

The following command types are known (hexadecimal values):

| Name | Hex | Description |
| :--- | :--- | :--- |
| `ZZ_MQTT_CMD_EVENT_NOTIFY` | `0x03e8` | Status updates (progress, errors) |
| `ZZ_MQTT_CMD_PRINT_SCHEDULE` | `0x03e9` | Print job scheduling |
| `ZZ_MQTT_CMD_FIRMWARE_VERSION` | `0x03ea` | Get firmware version |
| `ZZ_MQTT_CMD_NOZZLE_TEMP` | `0x03eb` | Set nozzle temperature (units: 1/100 °C) |
| `ZZ_MQTT_CMD_HOTBED_TEMP` | `0x03ec` | Set hotbed temperature (units: 1/100 °C) |
| `ZZ_MQTT_CMD_FAN_SPEED` | `0x03ed` | Set fan speed |
| `ZZ_MQTT_CMD_PRINT_SPEED` | `0x03ee` | Set print speed multiplier |
| `ZZ_MQTT_CMD_AUTO_LEVELING` | `0x03ef` | Start auto-leveling |
| `ZZ_MQTT_CMD_PRINT_CONTROL` | `0x03f0` | Start/Pause/Stop print |
| `ZZ_MQTT_CMD_FILE_LIST_REQUEST` | `0x03f1` | List files on SD card/USB |
| `ZZ_MQTT_CMD_GCODE_FILE_REQUEST` | `0x03f2` | Request specific GCode file |
| `ZZ_MQTT_CMD_ALLOW_FIRMWARE_UPDATE`| `0x03f3` | Trigger firmware update |
| `ZZ_MQTT_CMD_GCODE_FILE_DOWNLOAD` | `0x03fc` | Start GCode download |
| `ZZ_MQTT_CMD_Z_AXIS_RECOUP` | `0x03fd` | Z-axis offset/lift adjustment |
| `ZZ_MQTT_CMD_EXTRUSION_STEP` | `0x03fe` | Extrude/Retract filament |
| `ZZ_MQTT_CMD_ENTER_OR_QUIT_MATERIEL`| `0x03ff` | Filament change mode? |
| `ZZ_MQTT_CMD_MOVE_STEP` | `0x0400` | Manual axis movement |
| `ZZ_MQTT_CMD_MOVE_DIRECTION` | `0x0401` | Axis movement direction |
| `ZZ_MQTT_CMD_MOVE_ZERO` | `0x0402` | Homing (G28) |
| `ZZ_MQTT_CMD_APP_QUERY_STATUS` | `0x0403` | Query current printer status |
| `ZZ_MQTT_CMD_ONLINE_NOTIFY` | `0x0404` | Printer online status |
| `ZZ_MQTT_CMD_RECOVER_FACTORY` | `0x0405` | Factory reset |
| `ZZ_MQTT_CMD_BLE_ONOFF` | `0x0407` | Toggle Bluetooth |
| `ZZ_MQTT_CMD_DELETE_GCODE_FILE` | `0x0408` | Delete file from printer |
| `ZZ_MQTT_CMD_DEVICE_NAME_SET` | `0x040a` | Set printer nickname |
| `ZZ_MQTT_CMD_MOTOR_LOCK` | `0x040d` | Lock/Unlock stepper motors |
| `ZZ_MQTT_CMD_BREAK_POINT` | `0x040f` | Handle power loss recovery? |
| `ZZ_MQTT_CMD_AI_CALIB` | `0x0410` | AI camera calibration |
| `ZZ_MQTT_CMD_VIDEO_ONOFF` | `0x0411` | Toggle video AI monitoring |
| **`ZZ_MQTT_CMD_GCODE_COMMAND`** | **`0x0413`** | **Send raw GCode (Most versatile command)** |
| `ZZ_MQTT_CMD_PREVIEW_IMAGE_URL` | `0x0414` | Get/Set GCode preview image URL |
| `ZZ_MQTT_CMD_AI_SWITCH` | `0x041a` | Toggle AI features |

## Payload Examples

### Send raw GCode (`0x0413`)

```json
{
    "commandType": 1043,
    "cmdData": "G28 X Y",
    "cmdLen": 7
}
```

### Set Nozzle Temperature (`0x03eb`)

```json
{
    "commandType": 1003,
    "value": 21000
}
```
*(Note: Value is Celsius * 100)*

### Set Hotbed Temperature (`0x03ec`)

```json
{
    "commandType": 1004,
    "value": 6000
}
```
*(Note: Value is Celsius * 100)*
