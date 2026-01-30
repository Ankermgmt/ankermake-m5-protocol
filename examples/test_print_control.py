#!/usr/bin/env python3

import sys
sys.path.append(".")

import argparse
import json
import time
from datetime import datetime
from rich import print

from libflagship.util import enhex, unhex
from libflagship.mqtt import MqttMsg
from libflagship.mqttapi import AnkerMQTTBaseClient
import libflagship.httpapi

import cli.config

# inherit from AnkerMQTTBaseClient, and override event handling.
class AnkerMQTTClient(AnkerMQTTBaseClient):

    def on_connect(self, client, userdata, flags):
        print("[*] Connected to mqtt")

    def on_message(self, client, userdata, msg, pkt, tail):
        print(f"TOPIC [{msg.topic}]")
        # print(pkt) # Too verbose
        try:
            data = json.loads(pkt.data)
            print(f"DATA: {json.dumps(data, indent=2)}")
        except:
            print(f"RAW: {pkt.data}")

def parse_args():
    parser = argparse.ArgumentParser(description="Test Print Control")
    parser.add_argument("-v", "--value", type=int, required=True, help="Control value to send")
    parser.add_argument("-k", "--insecure", action="store_true")
    return parser.parse_args()

def main():
    args = parse_args()

    if args.insecure:
        import urllib3
        urllib3.disable_warnings()

    print("[*] Loading config..")
    mgr = cli.config.configmgr()
    with mgr.open() as cfg:
        if not cfg.account or not cfg.printers:
            print("No config/printers found. Please login first.")
            return
        
        printer_info = cfg.printers[0]
        account = cfg.account

        printer_sn = printer_info.sn
        mqtt_key = printer_info.mqtt_key
        mqtt_username = account.mqtt_username
        mqtt_password = account.mqtt_password
        nick_name = account.email # Fallback? Account object might not have nickname easily available

    print(f"[*] Connecting to {printer_sn}...")
    
    client = AnkerMQTTClient.login(printer_sn, mqtt_username, mqtt_password, mqtt_key, verify=not args.insecure)
    
    server = "make-mqtt-eu.ankermake.com" if account.region == "eu" else "make-mqtt.ankermake.com"
    client.connect(server)

    # Allow some time to connect
    client.fetch(timeout=2.0)

    # Construct the command
    # ZZ_MQTT_CMD_PRINT_CONTROL = 1008
    cmd = {
        "commandType": 1008,
        "data": {
            "value": args.value,
            "userName": nick_name,
            # "filePath": "" # Optional?
        }
    }

    print(f"[*] Sending command: {json.dumps(cmd)}")
    client.command(cmd)

    print("[*] Waiting for response...")
    start = datetime.now()
    while (datetime.now() - start).total_seconds() < 10:
        client.fetch(timeout=1.0)

if __name__ == "__main__":
    main()
