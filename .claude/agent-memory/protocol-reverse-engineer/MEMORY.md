# Protocol Reverse Engineer Memory

## Firmware Analysis: ACCELERATION_CONTROL (Confirmed 2026-02-21)

**What it is:** A safety clamp on M204 acceleration values. NOT vibration compensation or input shaping.
- Defined in `ANKER_Config.h` as `#define ACCELERATION_CONTROL 1`
- Only used in `M200-M205.cpp` inside `GcodeSuite::M204()`
- Clamps S/P/R/T values to `[0.1, default_accel]` range; resets to default if out of range
- `default_accel` depends on Linear Advance version: 2500 (normal) or 6000 (LA v2+)
- NOT used in M201 (max accel per axis) or M205 (jerk) -- only M204

## Anker Custom M-Codes (from anker_gcode/ directory)
- **M116**: Firmware/board version query (S0=FW, S1=board, S2=chip)
- **M1800/M1801**: Enable/disable debug logging
- **M2000-M2008**: Hardware control (probe, buffer info, board check, Z sensorless, homing, TMC config, extruder pos)
- **M2030/M2031**: Linear advance parameter get/set (A-F float params into `lin_parameter[]` array)
- **M3001-M3009**: Nozzle board comms (thresholds, FW version, heartbeat, bootloader CRC)
- **M3030-M3034**: Debug logging, production mode, probe offset, bed level temp, clog detection
- **M4201**: Set max acceleration per axis (with LA_V1 limits)
- **M4203**: Set max feedrate per axis (with LA_V1 limits)
- **M4204**: Set acceleration types (P/R/T) -- parallel to M204
- **M4205**: Advanced settings (jerk, segment time) -- parallel to M205
- **M4899**: Linear Advance version switch (0-3), resets all accel/jerk/feedrate to version defaults
- **M4900**: Wrapper for M900 (standard Linear Advance K-factor)

## Firmware Configuration Defaults (from Configuration.h)
- DEFAULT_ACCELERATION: 2500 mm/s^2
- DEFAULT_MAX_ACCELERATION: {2500, 2500, 100, 2500} (X,Y,Z,E)
- LA_V1_DEFAULT_ACCELERATION: 6000 mm/s^2
- LA_V1_DEFAULT_MAX_ACCELERATION: {6000, 6000, 100, 4000}
- CLASSIC_JERK enabled: X=15, Y=15, Z=0.3, E=3.0
- S_CURVE_ACCELERATION: enabled
- ANKER_E_SMOOTH: enabled (smooths LA K-value acceleration)
- ANKER_LIN_PARAMETER: enabled (K=0.20)

## Key Architecture Notes
- Generated files: libflagship/mqtt.py, pppp.py, amtypes.py, static/libflagship.js -- NEVER edit manually
- Use `make update` / `make diff` for spec changes
- Web services use borrow() context manager pattern
- All custom Anker M-codes gated behind `#if ENABLED(ANKER_MAKE_API)`

## Project File Paths
- Main entry: `/data_hdd/ankermake-m5-protocol-django1982/ankerctl.py`
- Protocol specs: `specification/mqtt.stf`, `specification/pppp.stf`
- MQTT commands doc: `documentation/MQTT_COMMANDS.md`
