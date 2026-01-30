# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
 - Apprise notification integration with full web UI configuration
   - Event hooks for print start/finish/fail/progress and file uploads
   - Snapshot attachments for notifications (with fallback to preview image)
   - Configurable progress interval and event toggles
   - Support for environment variable overrides (`APPRISE_*`)
 - Email/password login flow as alternative to `login.json` import
   - CAPTCHA handling via browser when required
   - Support for different country regions
 - Native print stop command via MQTT (`ZZ_MQTT_CMD_PRINT_CONTROL`)
 - Print control visibility toggle in web UI (configurable via `PRINT_CONTROLS_VISIBLE`)
 - Test script for print control commands (`examples/test_print_control.py`)
 - Comprehensive CLAUDE.md guide for AI assistants and developers

### Fixed
 - **PPPP single-reader architecture** - Critical fix for "two readers one socket" bug that caused packet loss and unstable video/command connections
 - Thread-safety in PPPP AABB reply reader with locking to prevent `EOFError` crashes
 - UDP socket timeout leak in PPPP recv/send operations
 - Race conditions in `Service.tap()` handler removal
 - WebSocket URL fixes for `/ws/video` and `/ws/ctrl` (missing `//`)
 - Camera light control null check to prevent errors before PPPP connection established
 - Video frame forwarding from XZYH to VideoQueue
 - File transfer EOF/OSError handling (now properly reported as ConnectionError)
 - Stop button reliability with improved multi-GCode command handling
 - PPPP service worker start logic to prevent "No pppp connection" errors during uploads

### Performance
 - Skip expensive notification operations when events are disabled
 - Optimized progress notification emission to respect interval settings

## [1.0.1] - 2024-01-15

 - Fixes MQTT connection errors post AnkerMake Firmware Upgrades

## [1.0.0] - 2023-05-24

 - Version 1.0.0!
 - Add video streaming support to web ui
 - Add support for uploading `login.json` through web ui
 - Add print monitoring through web ui
 - Add new mqtt types to libflagship
 - Add status icons for mqtt, pppp and ctrl websocket
 - Add support for restarting web services through web ui
 - Add support for turning on/off camera light from web ui
 - Add support for controlling video mode (sd/hd) from web ui
 - Add `--pppp-dump` option for making a debug packet capture
 - Stabilized video streaming, by fixing some rare corner cases.
 - Make video stream automatically reconnect on connection loss
 - Make video stream automatically suspend when no clients are connected

## [0.9.0] - 2023-04-17

 - First version with github actions for building docker image. (thanks to @cisien)
 - Add python version checking code, to prevent confusing errors if python version is too old.

## [0.8.0] - 2023-04-06

 - First version with built-in webserver! (thanks to @lazemss for the idea and proof-of-concept)
 - Webserver implements a few OctoPrint endpoints, allowing printing directly from PrusaSlicer.
 - Added static web contents, including step-by-step guide for setting up PrusaSlicer.

## [0.7.0] - 2023-04-04

 - First version with camera streaming support!
 - Fixed many bugs in the file upload code, including ability to send files larger than 512K.
 - Fixed file transfers on Windows platforms.

## [0.6.0] - 2023-04-03

 - First version that can send print jobs to the printer over pppp!
 - Completely reworked pppp api implementation.
 - Added support for upgrading config files automatically, when possible.
 - Major code refactoring and improvements.

## [0.5.0] - 2023-03-26

 - Officially licensed as GPLv3.
 - Improved documentation.
 - Much improved documentation (thanks to @austinrdennis).
 - Added `mqtt gcode` command, making it possible to send custom gcode to the printer!
 - Added `mqtt rename-printer` command.
 - Added `pppp lan-search` command.
 - Added `http calc-check-code` command.
 - Added `http calc-sec-code` command.

## [0.4.0] - 2023-03-22

 - First version with the command line tool: `ankerctl.py`.
 - Added `mqtt monitor` command.
 - Added `config import` command.
 - Added `config show` command.
 - Many fixes and improvements from @spuder.

## [0.3.0] - 2023-03-12

 - Examples moved to `examples/`.
 - Added example program that imports `login.json` from Ankermake Slicer.

## [0.3.0] - 2023-03-09

 - First version with a demo program, showing how to parse pppp packets.

## [0.1.0] - 2023-03-07

 - Early code for libflagship, and first version with a README.
