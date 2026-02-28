#!/usr/bin/env python3
"""Probe undocumented PPPP commands on AnkerMake M5 printer.

Reconnects for each command since the printer drops the connection
after receiving unknown command types.
"""

import json
import sys
import time
import logging

sys.path.insert(0, ".")

import cli.config
import cli.pppp
from libflagship.pppp import P2PCmdType

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

PROBE_CMDS = [
    (0x0462, "APP_CMD_GET_ADMIN_PWD"),
    (0x0463, "APP_CMD_GET_WIFI_PWD"),
    (0x0464, "APP_CMD_GET_EXCEPTION_LOG"),
    (0x0461, "APP_CMD_GET_UPDATE_STATUS"),
    (0x0465, "APP_CMD_GET_NEWVESION"),
    (0x044c, "APP_CMD_GET_ASEKEY"),
    (0x044e, "APP_CMD_SDINFO"),
    (0x044f, "APP_CMD_CAMERA_INFO"),
    (0x0468, "APP_CMD_GET_HUB_NAME"),
    (0x0469, "APP_CMD_GET_DEVS_NAME"),
    (0x046a, "APP_CMD_GET_P2P_CONN_STATUS"),
]


def connect():
    config = cli.config.configmgr()
    return cli.pppp.pppp_open(config, 0, timeout=10)


def probe_one(cmd_type, cmd_name):
    """Connect, send one command, collect response, disconnect."""
    log.info(f"--- {cmd_name} (0x{cmd_type:04x}) ---")

    try:
        api = connect()
    except Exception as e:
        log.error(f"  Connect failed: {e}")
        return {"cmd": cmd_name, "status": "connect_fail", "data": str(e)}

    payload = json.dumps({"commandType": cmd_type}).encode()
    log.info(f"  TX: {payload}")

    try:
        api.send_xzyh(payload, cmd=P2PCmdType.P2P_JSON_CMD, chan=0)
    except Exception as e:
        log.error(f"  Send failed: {e}")
        api.stop()
        return {"cmd": cmd_name, "status": "send_fail", "data": str(e)}

    # Collect responses for up to 3 seconds
    responses = []
    deadline = time.time() + 3.0
    while time.time() < deadline:
        try:
            resp = api.recv_xzyh(chan=0, timeout=0.5)
            if resp:
                raw = resp.data
                try:
                    parsed = json.loads(raw)
                    log.info(f"  RX (JSON): {json.dumps(parsed, indent=2)}")
                    responses.append({"type": "json", "data": parsed})
                except (json.JSONDecodeError, UnicodeDecodeError):
                    log.info(f"  RX (hex): {raw.hex()}")
                    log.info(f"  RX (len): {len(raw)} bytes")
                    # Try printing as string with errors replaced
                    log.info(f"  RX (str): {raw.decode('utf-8', errors='replace')}")
                    responses.append({"type": "binary", "hex": raw.hex(), "len": len(raw)})
        except Exception:
            break

    try:
        api.stop()
    except Exception:
        pass

    if not responses:
        log.info(f"  No response")
        return {"cmd": cmd_name, "status": "no_response"}

    return {"cmd": cmd_name, "status": "ok", "responses": responses}


def main():
    log.info("PPPP Command Probe - AnkerMake M5\n")

    results = []
    for cmd_type, cmd_name in PROBE_CMDS:
        result = probe_one(cmd_type, cmd_name)
        results.append(result)
        time.sleep(2)  # Let the printer recover between connections

    log.info("\n" + "=" * 60)
    log.info("SUMMARY")
    log.info("=" * 60)
    for r in results:
        if r["status"] == "ok":
            log.info(f"  [RESPONSE] {r['cmd']}: {r['responses']}")
        else:
            log.info(f"  [{r['status'].upper()}] {r['cmd']}")

    # Dump full results as JSON
    log.info("\nFull JSON results:")
    log.info(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
