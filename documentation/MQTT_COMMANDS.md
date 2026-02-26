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
| `ZZ_MQTT_CMD_FIRMWARE_VERSION` | `0x03ea` | Get firmware version string |
| `ZZ_MQTT_CMD_NOZZLE_TEMP` | `0x03eb` | Set nozzle temperature (units: 1/100 °C) |
| `ZZ_MQTT_CMD_HOTBED_TEMP` | `0x03ec` | Set hotbed temperature (units: 1/100 °C) |
| `ZZ_MQTT_CMD_FAN_SPEED` | `0x03ed` | Set fan speed |
| `ZZ_MQTT_CMD_PRINT_SPEED` | `0x03ee` | Set print speed multiplier |
| `ZZ_MQTT_CMD_AUTO_LEVELING` | `0x03ef` | Start auto-leveling procedure |
| `ZZ_MQTT_CMD_PRINT_CONTROL` | `0x03f0` | Print state control: value=2 pause, value=3 resume, value=4 stop/cancel, value=0 restart from beginning |
| `ZZ_MQTT_CMD_FILE_LIST_REQUEST` | `0x03f1` | List files on SD card (value=1) or USB (value≠1) |
| `ZZ_MQTT_CMD_GCODE_FILE_REQUEST` | `0x03f2` | Request specific GCode file |
| `ZZ_MQTT_CMD_ALLOW_FIRMWARE_UPDATE` | `0x03f3` | Trigger firmware update |
| `ZZ_MQTT_CMD_GCODE_FILE_DOWNLOAD` | `0x03fc` | Start GCode download |
| `ZZ_MQTT_CMD_Z_AXIS_RECOUP` | `0x03fd` | Z-axis offset/lift adjustment |
| `ZZ_MQTT_CMD_EXTRUSION_STEP` | `0x03fe` | Run extrusion stepper (extrude/retract) |
| `ZZ_MQTT_CMD_ENTER_OR_QUIT_MATERIEL` | `0x03ff` | Filament change mode |
| `ZZ_MQTT_CMD_MOVE_STEP` | `0x0400` | Manual axis movement (step) |
| `ZZ_MQTT_CMD_MOVE_DIRECTION` | `0x0401` | Axis movement direction |
| `ZZ_MQTT_CMD_MOVE_ZERO` | `0x0402` | Homing — move to home position (G28) |
| `ZZ_MQTT_CMD_APP_QUERY_STATUS` | `0x0403` | Query current printer status |
| `ZZ_MQTT_CMD_ONLINE_NOTIFY` | `0x0404` | Printer online status |
| `ZZ_MQTT_CMD_RECOVER_FACTORY` | `0x0405` | **Factory reset** (use `--force` flag) |
| `ZZ_MQTT_CMD_BLE_ONOFF` | `0x0407` | Enable/disable Bluetooth (BLE) |
| `ZZ_MQTT_CMD_DELETE_GCODE_FILE` | `0x0408` | Delete specified GCode file from printer |
| `ZZ_MQTT_CMD_RESET_GCODE_PARAM` | `0x0409` | Reset GCode parameters (purpose unclear) |
| `ZZ_MQTT_CMD_DEVICE_NAME_SET` | `0x040a` | Set printer nickname (`devName` field required) |
| `ZZ_MQTT_CMD_DEVICE_LOG_UPLOAD` | `0x040b` | Upload device logs |
| `ZZ_MQTT_CMD_ONOFF_MODAL` | `0x040c` | Unknown modal toggle |
| `ZZ_MQTT_CMD_MOTOR_LOCK` | `0x040d` | Lock/Unlock stepper motors |
| `ZZ_MQTT_CMD_PREHEAT_CONFIG` | `0x040e` | Preheat configuration |
| `ZZ_MQTT_CMD_BREAK_POINT` | `0x040f` | Power loss recovery handling |
| `ZZ_MQTT_CMD_AI_CALIB` | `0x0410` | AI camera calibration |
| `ZZ_MQTT_CMD_VIDEO_ONOFF` | `0x0411` | Toggle video/AI monitoring |
| `ZZ_MQTT_CMD_ADVANCED_PARAMETERS` | `0x0412` | Advanced printer parameters |
| **`ZZ_MQTT_CMD_GCODE_COMMAND`** | **`0x0413`** | **Send raw GCode (most versatile command)** |
| `ZZ_MQTT_CMD_PREVIEW_IMAGE_URL` | `0x0414` | Get/Set GCode preview image URL |
| `ZZ_MQTT_CMD_SYSTEM_CHECK` | `0x0419` | System health check |
| `ZZ_MQTT_CMD_AI_SWITCH` | `0x041a` | Toggle AI features |
| `ZZ_MQTT_CMD_AI_INFO_CHECK` | `0x041b` | AI information check |
| `ZZ_MQTT_CMD_MODEL_LAYER` | `0x041c` | Model layer information |
| `ZZ_MQTT_CMD_MODEL_DL_PROCESS` | `0x041d` | Model download process |
| `ZZ_MQTT_CMD_PRINT_MAX_SPEED` | `0x041f` | Maximum print speed setting |
| `ZZ_MQTT_CMD_ALEXA_MSG` | `0x0bb8` | Alexa voice assistant integration |

## Printer Notification Types

The following `commandType` values are emitted by the printer as unsolicited status updates (notifications). They are not sent as commands.

| commandType (decimal) | Hex | Field(s) | Description |
| :--- | :--- | :--- | :--- |
| `1000` | `0x03e8` | `value` | Printer state machine: `0` = idle/finished, `1` = active/printing, `2` = paused, `8` = aborted (user cancelled via touchscreen or calibration phase) |
| `1001` | `0x03e9` | `time` | Remaining print time in seconds |
| `1003` | `0x03eb` | `currentTemp`, `targetTemp` | Nozzle temperature (units: 1/100 °C) |
| `1004` | `0x03ec` | `currentTemp`, `targetTemp` | Hotbed temperature (units: 1/100 °C) |
| `1006` | `0x03ee` | `value` | Print speed in mm/s |
| `1007` | `0x03ef` | `value` | Auto-leveling probe progress — emitted after each probe point during G29; `value` = current point index (50 total: 1 initial center probe + 7×7 grid). Use this to display a live progress bar. |
| `1044` | `0x0414` | `filePath` | GCode file path — sent when a print job starts; basename is used as the filename |
| `1052` | `0x041c` | `real_print_layer`, `total_layer` | Current and total layer counts; derive print progress from these |

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

### Print Control (`0x03f0`)

Empirically verified values (2026-02-24):

```json
{"commandType": 1008, "value": 2}
```

| value | Action | Notes |
|-------|--------|-------|
| `0` | Restart print from beginning | Does NOT stop — restarts the job |
| `2` | Pause print | Printer enters paused state; ct=1000 value=2 confirms |
| `3` | Resume print | Returns to printing; ct=1000 value=1 confirms |
| `4` | Stop / cancel print | Terminates the job |

`reply=0` = command received (not necessarily executed). `reply=6` = invalid command.
Sending via PPPP P2P_JSON_CMD returns error `0x2710` — use MQTT only for print control.
