# Repository Guidelines

## Project Structure & Module Organization
- `ankerctl.py` is the main CLI entrypoint.
- `cli/` contains command implementations and helpers.
- `web/` hosts the Flask web server, services, and UI routes.
- `libflagship/` implements protocol clients (MQTT, PPPP, HTTP).
- `static/` contains web UI assets (JS/CSS/images) and vendor bundles.
- `specification/` and `templates/` define protocol specs and codegen templates.
- `examples/` holds small scripts for manual protocol tests and demos.

## Build, Test, and Development Commands
- `./ankerctl.py webserver run` starts the local web UI (requires config).
- `./ankerctl.py mqtt monitor` or `./ankerctl.py pppp lan-search` are quick CLI smoke checks.
- `docker compose up` builds/runs the container from `docker-compose.yaml` (host networking).
- `make update` regenerates `libflagship/` and `static/` from `specification/`.
- `make diff` shows codegen deltas without writing.
- `make install-tools` installs the `transwarp` generator dependency.

## Coding Style & Naming Conventions
- Python uses 4-space indentation; follow existing module layout and patterns.
- Prefer snake_case for functions/variables and CapWords for classes.
- JavaScript follows existing style in `static/ankersrv.js`; avoid introducing new frameworks.
- No enforced formatter or linter is configured; keep diffs tight and readable.

## Testing Guidelines
- There is no automated test suite in this repo today.
- Validate changes manually using the CLI (`./ankerctl.py ...`) and web UI.
- For protocol changes, use scripts in `examples/` to reproduce behavior.

## Commit & Pull Request Guidelines
- Git history uses short, descriptive commit messages (sentence case, sometimes with issue IDs).
- Keep commits focused; mention affected area (e.g., "Fix PPPP file upload reply handling").
- PRs should include a brief summary, testing notes, and screenshots for UI changes.

## Configuration & Security Notes
- Config is stored under `~/.config/ankerctl` (or the container volume).
- `login.json` contains sensitive data; never commit it or paste it in issues.
