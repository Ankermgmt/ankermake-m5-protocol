""" This module provides MQTT-related functionality for interacting with AnkerMake printers. \
    It imports necessary modules, defines constants, and implements functions for opening an \
    MQTT connection, executing MQTT commands, and handling responses.

Functions:

mqtt_open: Opens an MQTT connection to the AnkerMake printer, authenticating with the provided configuration.
mqtt_command: Sends a given command to the printer via the MQTT connection and handles the response, if any.

Constants:

ROOT_DIR: The root directory, loaded from the config module.
servertable: A dictionary mapping printer regions to their respective MQTT server URLs. """
from os import path
import logging as log
import click

from config import ROOT_DIR
import cli.util

from libflagship.mqttapi import AnkerMQTTBaseClient

servertable = {
    "eu": "make-mqtt-eu.ankermake.com",
    "us": "make-mqtt.ankermake.com",
}


def mqtt_open(config, insecure):
    cert_path = path.join(ROOT_DIR, "ssl/ankermake-mqtt.crt")

    with config.open() as cfg:
        printer = cfg.printers[0]
        acct = cfg.account
        server = servertable[acct.region]
        log.info(f"Connecting to {server}")
        client = AnkerMQTTBaseClient.login(
            printer.sn,
            acct.mqtt_username,
            acct.mqtt_password,
            printer.mqtt_key,
            ca_certs=cert_path,
            verify=not insecure,
        )
        client.connect(server)
        return client


def mqtt_command(client, msg):
    client.command(msg)

    reply = client.await_response(msg["commandType"])
    if reply:
        click.echo(cli.util.pretty_json(reply))
    else:
        log.error("No response from printer")
