"""Module: config_manager

This module provides utility functions for importing, showing, and handling printer
configuration settings.

Classes:
- ConfigImportError: Raised when there is an error with the config api.

Functions:
- config_show(config): Takes a configuration object as input and returns a string
                    representation of the configuration.
- config_import(login_file, config): Loads the configuration from the API. login_file is a
                                    file object containing the user's login information,
                                    while config is a configuration object.
Returns:
- config_output: A formatted string containing the configuration information.
"""

import libflagship.httpapi
import libflagship.logincache

import cli.util
import cli.config


class ConfigImportError(Exception):
    """
    Raised when there is an error with the config api.
    """


def config_show(config: object):
    """
    Takes a configuration object as input and returns a string representation of the configuration.

    Args:
    - config: A configuration object.

    Returns:
    - config_output: A formatted string containing the configuration information.
    """
    config_output = f"""Account:
  user_id:    {config.account.user_id[:10]}...[REDACTED]
  auth_token: {config.account.auth_token[:10]}...[REDACTED]
  email:      {config.account.email}
  region:     {config.account.region.upper()}

"""
    config_output += "Printers:\n"
    for printer in config.printers:
        config_output += f"""\
  duid:      {printer.p2p_duid}
  sn:        {printer.sn}
  ip:        {printer.ip_addr}
  wifi_mac:  {cli.util.pretty_mac(printer.wifi_mac)}
"""
        config_output += "  api_hosts:\n"
        for host in printer.api_hosts:
            config_output += f"     - {host}\n"
        config_output += "  p2p_hosts:\n"
        for host in printer.p2p_hosts:
            config_output += f"     - {host}\n"
    return config_output


def config_import(login_file: object, config: object):
    """
    Loads the configuration from the API. login_file is a file object containing the user's login information,
    while config is a configuration object.

    Args:
    - login_file: A file object containing the user's login information.
    - config: A configuration object.

    Returns:
    - config_output: A formatted string containing the configuration information.
    """
    # extract auth token
    cache = libflagship.logincache.load(login_file.stream.read())["data"]
    auth_token = cache["auth_token"]

    # extract account region
    region = libflagship.logincache.guess_region(cache["ab_code"])

    try:
        new_config = cli.config.load_config_from_api(auth_token, region, False)
    except libflagship.httpapi.APIError as err:
        raise ConfigImportError(
            f"Config import failed: {err}. \
                Auth token might be expired: make sure Ankermake Slicer can connect, then try again")
    except Exception as err:
        raise ConfigImportError(f"Config import failed: {err}")

    try:
        config.save("default", new_config)
    except Exception as E:
        raise ConfigImportError(f"Config import failed: {E}")
    return new_config
