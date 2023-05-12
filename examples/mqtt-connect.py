#!/usr/bin/env python3

import sys             # nopep8
sys.path.append("..")  # nopep8

import argparse
import json
from rich import print

from libflagship.util import enhex, unhex
from libflagship.mqtt import MqttMsg
from libflagship.mqttapi import AnkerMQTTBaseClient

# inherit from AnkerMQTTBaseClient, and override event handling.
class AnkerMQTTClient(AnkerMQTTBaseClient):

    def on_connect(self, client, userdata, flags):
        print("[*] Connected to mqtt")

    def on_message(self, client, userdata, msg, pkt, tail):
        print(f"TOPIC \[{msg.topic}]")
        sys.stdout.buffer.write(enhex(msg.payload[:]).encode() + b"\n")

        print(pkt)

        if tail:
            print(f"UNPARSED TAIL DATA: {tail}")

def parse_args():
    def fmt(prog):
        return argparse.HelpFormatter(prog,max_help_position=42)

    parser = argparse.ArgumentParser(
        prog="mqtt-connect",
        description="Connect to Ankermake M5 mqtt server",
        formatter_class=fmt
    )

    parser.add_argument(
        "-r", "--region",
        choices=["eu", "us"],
        required=True,
        help="Select server region"
    )

    parser.add_argument(
        "-P", "--printer",
        help="Use specified printer serial (instead of first available)"
    )

    parser.add_argument(
        "-A", "--auth",
        help="Auth token"
    )

    parser.add_argument(
        "-k", "--insecure",
        action="store_const",
        const=True,
        default=False,
        help="Disable TLS certificate validation",
    )

    args = parser.parse_args()
    if args.auth and len(args.auth) != 48:
        print("ERROR: Auth token must be 48 characters")
        exit()

    return args

def find_printer(devices, printer):
    for dev in devices:
        if not printer:
            return dev
        if dev["station_sn"] == printer:
            return dev

def main():
    import libflagship.httpapi

    servertable = {
        "eu": "make-mqtt-eu.ankermake.com",
        "us": "make-mqtt.ankermake.com",
    }

    # parse arguments
    args = parse_args()

    if args.insecure:
        import urllib3
        urllib3.disable_warnings()

    print("[*] Initializing API..")
    # create api instances
    appapi = libflagship.httpapi.AnkerHTTPAppApiV1(auth_token=args.auth, region=args.region, verify=not args.insecure)
    ppapi = libflagship.httpapi.AnkerHTTPPassportApiV1(auth_token=args.auth, region=args.region, verify=not args.insecure)

    # request profile and printer list
    print("[*] Requesting profile data..")
    profile = ppapi.profile()

    print("[*] Requesting printer list..")
    printers = appapi.query_fdm_list()

    # find printer to monitor
    printer = find_printer(printers, args.printer)

    if not printer:
        print(f"ERROR: could not find printer [{args.printer}]")
        if printers:
            print(f"Available printers:")
            for printer in printers:
                print(f"  {printer['station_sn']}")
        exit()

    print("[*] Connecting to mqtt..")
    # collect mqtt arguments
    printer_sn    = printer["station_sn"]
    mqtt_username = "eufy_" + profile["user_id"]
    mqtt_password = profile["email"] # yes, your mqtt password is your email address..
    mqtt_key      = unhex(printer["secret_key"])

    # get up and running
    try:
        client = AnkerMQTTClient.login(printer_sn, mqtt_username, mqtt_password, mqtt_key, verify=args.insecure)
        client.connect(server=servertable[args.region])
        client.loop()
    except Exception as E:
        print(f"ERROR: {E}", file=sys.stderr)

if __name__ == "__main__":
    main()
