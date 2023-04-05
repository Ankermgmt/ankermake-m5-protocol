import json
import click
import logging as log

import cli.util

from libflagship.mqttapi import AnkerMQTTBaseClient

servertable = {
    "eu": "make-mqtt-eu.ankermake.com",
    "us": "make-mqtt.ankermake.com",
}


def mqtt_open(config, insecure):
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
            ca_certs="examples/ankermake-mqtt.crt",
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
