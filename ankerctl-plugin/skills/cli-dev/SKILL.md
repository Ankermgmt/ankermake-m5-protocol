---
name: cli-dev
description: Aktiviere bei CLI-Entwicklung, Click-Commands, neuen Befehlen, oder wenn "ankerctl.py", "CLI", "Click", "@pass_env" erwähnt wird.
version: 1.0.0
---

# CLI Development Skill

## Click CLI Pattern

```python
@main.group("groupname", help="Group description")
@pass_env
def groupname(env):
    env.load_config()

@groupname.command("subcommand")
@click.argument("arg", required=True)
@click.option("--flag", "-f", is_flag=True, help="Description")
@pass_env
def groupname_subcommand(env, arg, flag):
    """Docstring becomes help text."""
    # Implementation
```

## Environment Object (env)

| Attribut | Beschreibung |
|----------|--------------|
| `env.config` | Konfiguration |
| `env.printer_index` | Drucker-Index (0-based) |
| `env.insecure` | TLS-Verification Flag |
| `env.pppp_dump` | Debug Log Path |

## Wichtige Dateien

| Datei | Inhalt |
|-------|--------|
| ankerctl.py | Haupt-Entry-Point |
| cli/mqtt.py | MQTT-Befehle |
| cli/pppp.py | PPPP-Befehle |
| cli/config.py | Config-Befehle |
| cli/model.py | Datenmodelle (Account, Printer, Config) |
| cli/logfmt.py | Logging-Formatierung |
| cli/util.py | CLI-Utilities |

## CLI Quick Reference

```bash
# Configuration
./ankerctl.py config import [path/to/login.json]
./ankerctl.py config login [COUNTRY]
./ankerctl.py config show

# MQTT commands
./ankerctl.py mqtt monitor
./ankerctl.py mqtt gcode
./ankerctl.py mqtt rename-printer NAME

# PPPP commands
./ankerctl.py pppp lan-search
./ankerctl.py pppp print-file FILE
./ankerctl.py pppp capture-video -m 4mb output.h264

# Global options
./ankerctl.py -p INDEX ...    # Select printer by index
./ankerctl.py -k ...          # Disable TLS verification
./ankerctl.py -v/-q ...       # Verbosity
```

## Adding a New CLI Command

1. Add command function in appropriate module (`cli/mqtt.py`, `cli/pppp.py`, etc.)
2. Register with Click decorator (`@group.command()`)
3. Use `@pass_env` for environment access
4. Follow existing patterns for consistency
