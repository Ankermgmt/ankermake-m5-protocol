#!/usr/bin/env python3
"""
Print control test — send stop/pause/resume via MQTT and capture all responses.

Uses the same mqtt_open() / fetch() stack as ankerctl itself.
Also subscribes to /device/maker/{SN}/command so we can sniff what the
official AnkerMake App sends to the printer (same AES key, fully decryptable).

Run from project root:

    # Monitor only — watch ALL MQTT traffic including what the App sends:
    python3 examples/print_control_test.py --monitor

    # Send stop — try both payload formats (default):
    python3 examples/print_control_test.py --value 0

    # Send stop — flat format only  {"commandType": 1008, "value": 0}:
    python3 examples/print_control_test.py --value 0 --format flat

    # Send stop — nested format  {"commandType": 1008, "data": {"value": 0, ...}}:
    python3 examples/print_control_test.py --value 0 --format nested

    # Disable TLS verification:
    python3 examples/print_control_test.py --value 0 -k
"""

import sys
sys.path.append(".")

import argparse
import json
import time
from datetime import datetime

import cli.config
from cli.mqtt import mqtt_open


PRINT_CONTROL_CMD = 1008  # ZZ_MQTT_CMD_PRINT_CONTROL = 0x03f0
CONTROL_NAMES = {0: "STOP", 1: "PAUSE", 2: "RESUME"}


def ts():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def drain(client, seconds):
    """Poll MQTT for `seconds` seconds, print every received message."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        for msg, data_list in client.fetch(timeout=0.2):
            print()
            # Mark direction: >>> = App→Printer (device topic), <<< = Printer→us (phone topic)
            direction = ">>>" if "/device/maker/" in msg.topic else "<<<"
            print(f"[{ts()}] {direction} TOPIC: {msg.topic}")
            for data in data_list:
                print(f"[{ts()}]     PAYLOAD:\n{json.dumps(data, indent=2)}")


def build_flat(value):
    """Format A — flat value (what send_print_control in mqtt.py currently sends)."""
    return {"commandType": PRINT_CONTROL_CMD, "value": value}


def build_nested(value, username):
    """Format B — nested data.value (original example script / Gemini attempt)."""
    return {"commandType": PRINT_CONTROL_CMD, "data": {"value": value, "userName": username}}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Test ZZ_MQTT_CMD_PRINT_CONTROL (0x03f0)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--value", "-v", type=int, choices=[0, 1, 2], metavar="{0,1,2}",
        help="Control value: 0=STOP  1=PAUSE  2=RESUME",
    )
    group.add_argument(
        "--monitor", "-m", action="store_true",
        help="Monitor only — do not send any command",
    )
    parser.add_argument(
        "--format", "-f", choices=["flat", "nested", "both"], default="both",
        help="Payload format: flat | nested | both (default: both — flat first, then nested)",
    )
    parser.add_argument(
        "--wait", "-w", type=float, default=2.0,
        help="Seconds to wait after connect before sending (default: 2.0)",
    )
    parser.add_argument(
        "--listen", "-l", type=float, default=10.0,
        help="Seconds to listen after sending (default: 10.0)",
    )
    parser.add_argument(
        "--insecure", "-k", action="store_true",
        help="Disable TLS certificate validation",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.insecure:
        import urllib3
        urllib3.disable_warnings()

    # Load username for nested format (email is used as userName)
    mgr = cli.config.configmgr()
    with mgr.open() as cfg:
        if not cfg.account or not cfg.printers:
            print("ERROR: No config/printers found. Run 'ankerctl config import' first.")
            sys.exit(1)
        username = cfg.account.email
        printer_sn = cfg.printers[0].sn

    print(f"[*] Printer SN: {printer_sn}")

    if args.value is not None:
        label = CONTROL_NAMES.get(args.value, "?")
        print(f"[*] Command:    PRINT_CONTROL value={args.value} ({label}), format={args.format}")

    print(f"[*] Connecting via mqtt_open()...")
    client = mqtt_open(mgr, printer_index=0, insecure=args.insecure)

    # Also subscribe to the device command topic so we can sniff the official App.
    # Messages are encrypted with the same printer MQTT key — fully decryptable.
    device_cmd_topic = f"/device/maker/{client.sn}/command"
    client._mqtt.subscribe(device_cmd_topic)
    print(f"[*] Extra subscription: {device_cmd_topic}")

    # Settle — collect any initial status messages from the printer
    print(f"[*] Waiting {args.wait}s for initial messages...")
    drain(client, args.wait)

    if not args.monitor and args.value is not None:
        to_send = []
        if args.format in ("flat", "both"):
            to_send.append(("flat  ", build_flat(args.value)))
        if args.format in ("nested", "both"):
            to_send.append(("nested", build_nested(args.value, username)))

        for fmt_label, cmd in to_send:
            print()
            print(f"[{ts()}] >>> Sending [{fmt_label}]: {json.dumps(cmd)}")
            client.command(cmd)
            drain(client, 1.0)

    print(f"\n[*] Listening for responses ({args.listen}s)...")
    drain(client, args.listen)

    print(f"\n[*] Done.")


if __name__ == "__main__":
    main()
