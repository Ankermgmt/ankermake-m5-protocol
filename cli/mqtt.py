import click
import logging

log = logging.getLogger("cli.mqtt")


import cli.util

from libflagship import ROOT_DIR
from libflagship.mqttapi import AnkerMQTTBaseClient

servertable = {
    "eu": "make-mqtt-eu.ankermake.com",
    "us": "make-mqtt.ankermake.com",
}


def mqtt_open(config, printer_index, insecure):

    with config.open() as cfg:
        if printer_index >= len(cfg.printers):
            log.critical(f"Printer number {printer_index} out of range, max printer number is {len(cfg.printers)-1} ")
        printer = cfg.printers[printer_index]
        acct = cfg.account
        server = servertable[acct.region]
        log.info(f"Connecting printer {printer.name} ({printer.p2p_duid}) through {server}")
        client = AnkerMQTTBaseClient.login(
            printer.sn,
            acct.mqtt_username,
            acct.mqtt_password,
            printer.mqtt_key,
            ca_certs=ROOT_DIR / "ssl/ankermake-mqtt.crt",
            verify=not insecure,
        )
        client.connect(server)
        return client


def mqtt_gcode_dump(client, gcode, collect_window=3.0):
    """Send a GCode command and collect all response packets.

    Unlike mqtt_command, this waits for multiple MQTT responses and
    concatenates their resData fields to reconstruct the full ring-buffer
    output. Useful for commands that generate long responses (M503, M420 V).
    """
    from libflagship.mqtt import MqttMsgType
    cmd = {
        "commandType": MqttMsgType.ZZ_MQTT_CMD_GCODE_COMMAND.value,
        "cmdData": gcode,
        "cmdLen": len(gcode),
    }
    client.command(cmd)
    msgs = client.await_responses(MqttMsgType.ZZ_MQTT_CMD_GCODE_COMMAND, collect_window=collect_window)
    return msgs


def mqtt_command(client, msg):
    client.command(msg)

    reply = client.await_response(msg["commandType"])
    if reply:
        click.echo(cli.util.pretty_json(reply))
    else:
        log.error("No response from printer")


def mqtt_query(client, msg):
    client.query(msg)

    reply = client.await_response(msg["commandType"])
    if reply:
        click.echo(cli.util.pretty_json(reply))
    else:
        log.error("No response from printer")
