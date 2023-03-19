#!/usr/bin/env python3

import click
import logging

import cli.config
import cli.model
import cli.logfmt

@click.group()
@click.pass_context
def main(ctx):
    ctx.obj = cli.config.configmgr()

@main.group("mqtt", help="Low-level mqtt api access")
def mqtt(): pass

@main.group("pppp", help="Low-level pppp api access")
def pppp(): pass

@main.group("http", help="Low-level http api access")
def http(): pass

@main.group("config", help="View and update configuration")
def config(): pass

@config.command("import")
@click.argument("filename", required=False)
@click.pass_obj
def config_import(obj, filename):
    """Import printer and account information from login.json"""
    print(f"config_import {filename}")

@config.command("show")
@click.pass_obj
def config_show(cfg):
    """Show current config"""

    with cfg.printers() as printers:
        if printers:
            print("Printers:")
            for p in printers:
                print(f"  {p}")
        else:
            log.error("No printers configured. Run 'config import' to populate.")

if __name__ == "__main__":
    log = cli.logfmt.setup_logging()
    main()
