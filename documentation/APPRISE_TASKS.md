# Apprise Integration Tasks

## Overview
These tasks follow `documentation/APPRISE_INTEGRATION_PLAN.md`. All UI text stays in English for now.

## Task 1: Config schema + merge on import
**Goal:** Persist `notifications.apprise` in `default.json` and keep it during `config import`.

**Scope**
- Add defaults for `notifications.apprise` when config is missing.
- Ensure `config import` merges existing `notifications.apprise` instead of overwriting it.

**Files**
- `cli/config.py`
- `cli/model.py` (optional: defaults/helpers)
- `ankerctl.py` (config import flow)
- `web/config.py` (web import flow)

**Acceptance criteria**
- Running `config import` keeps `notifications.apprise` intact.
- New configs get sensible defaults for `notifications.apprise`.

---

## Task 2: Apprise HTTP client
**Goal:** Add a lightweight HTTP client with env overrides and template formatting.

**Scope**
- Implement `libflagship/notifications/apprise_client.py`.
- Add `libflagship/notifications/events.py` for event constants.
- Support env overrides (`APPRISE_*`).

**Files**
- `libflagship/notifications/__init__.py`
- `libflagship/notifications/apprise_client.py`
- `libflagship/notifications/events.py`

**Acceptance criteria**
- `AppriseClient.is_enabled()` returns true only when required fields are present.
- `send()` formats templates and posts to `{server_url}/notify/{key}`.
- `test_connection()` returns a status and message.

---

## Task 3: Web API for settings + test
**Goal:** Expose endpoints to load/save/test Apprise settings.

**Scope**
- Add API routes in `web/__init__.py`.
- Read/write config through `cli.config` manager (no hardcoded paths).

**Endpoints**
- `GET /api/notifications/settings`
- `POST /api/notifications/settings`
- `POST /api/notifications/test`

**Acceptance criteria**
- Settings are persisted to `default.json`.
- Test endpoint returns success/failure with a human‑readable message.

---

## Task 4: Setup tab UI + JS
**Goal:** Add Notifications section with side navigation.

**Scope**
- Add Setup side nav (Printer / Notifications) with anchor IDs.
- Notifications form with enabled toggle, server URL, key, events, progress interval, include image.
- Buttons: Save / Test.
- JS to load/save/test via API.

**Files**
- `static/tabs/setup.html`
- `static/ankersrv.js`
- `static/ankersrv.css` (minimal additions if needed)

**Acceptance criteria**
- Settings load on page open and can be saved.
- Test button sends a test notification.
- Layout works on desktop and mobile (side nav collapses gracefully).

---

## Task 5: Event hooks (MQTT + upload)
**Goal:** Emit notifications from real events.

**Scope**
- Print start/finish/fail/progress from MQTT stream.
- Upload completion from file transfer service.
- Progress notifications respect interval.

**Files**
- `web/service/mqtt.py` (or a new monitor helper)
- `web/service/filetransfer.py`

**Acceptance criteria**
- Notifications fire only for enabled events.
- Progress notifications respect `interval_percent`.

---

## Task 6 (Phase 2): Snapshot attachments (optional)
**Goal:** Attach camera snapshots to progress/finish notifications.

**Scope**
- Capture snapshot from existing video/PPPP support.
- Encode and send as `attach` if enabled.
- Clean up temp files.

**Acceptance criteria**
- Notifications with attachments work when enabled; falls back to text only when not available.

---

## Task 7: Docs & validation
**Goal:** Document usage and verify with a real printer.

**Scope**
- Add README section (quick setup + env vars).
- Add brief validation steps.

**Acceptance criteria**
- Docs include config + Docker env examples.
- Manual test checklist is clear.
