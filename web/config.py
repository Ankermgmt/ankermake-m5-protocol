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
    config_output = f"""<p>Account:</p><p>
        user_id:    {config.account.user_id[:10]}...[REDACTED] <br/>
        auth_token: {config.account.auth_token[:10]}...[REDACTED] <br/>
        email:      {config.account.email} <br/>
        region:     {config.account.region.upper()} </p
    """
    config_output += "<p>Printers:</p><hr/>"
    for printer in config.printers:
        config_output += f"""<p>
            duid:      {printer.p2p_duid} <br/>
            sn:        {printer.sn} <br/>
            ip:        {printer.ip_addr} <br/>
            wifi_mac:  {cli.util.pretty_mac(printer.wifi_mac)} <br/>
            api_hosts: {', '.join(printer.api_hosts)} <br/>
            p2p_hosts: {', '.join(printer.p2p_hosts)} <hr/></p>
        """
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
