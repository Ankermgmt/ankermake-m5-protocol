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
- config_login(email, password, country, captcha_id, captcha_answer, config):
                                     Loads the login information as well as the
                                     configration from the API.
"""
import libflagship.httpapi
import libflagship.logincache

import cli.util
import cli.config
import cli.countrycodes


class ConfigImportError(Exception):
    """
    Raised when there is an error with the config api.
    """
    def __init__(self, *args, **kwargs):
        if "captcha" in kwargs:
            self.captcha = kwargs["captcha"]
            del kwargs["captcha"]
            args = list(args)
            args.append(self.captcha)
        else:
            self.captcha = None

        super().__init__(*args)


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
  country:    {config.account.country.upper()}

"""
    config_output += "Printers:\n"
    for i, printer in enumerate(config.printers):
        config_output += f"""\
  printer:   {i}
  id:        {printer.id}
  name:      {printer.name}
  duid:      {printer.p2p_duid}
  sn:        {printer.sn}
  model:     {printer.model}
  created:   {printer.create_time}
  updated:   {printer.update_time}
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

    # get the login data
    cache = libflagship.logincache.load(login_file.stream.read())["data"]

    # load remaining configuration items from the server
    cli.config.import_config_from_server(config, cache, False)


def config_login(email: str, password: str, country: str, captcha_id: str, captcha_answer: str, config: object):
    """
    Loads the login information and then the configuration from the API.

    Args:
    - email: The user's email address.
    - password: The user's password.
    - country: The 2-letter country code.
    - captcha_id: The ID of the captcha, empty if no captcha to solve
    - captcha_answer: The textual answer to the captcha
    - config: A configuration object.
    """
    # extract account region
    region = libflagship.logincache.guess_region(country)

    try:
        login = cli.config.fetch_config_by_login(email, password, region, False, captcha_id, captcha_answer)
    except libflagship.httpapi.APIError as E:
        # check if the error is actually a request to solve a captcha
        if E.json and "data" in E.json:
            data = E.json["data"]
            if "captcha_id" in data:
                raise ConfigImportError(str(E), captcha={
                    "id": data["captcha_id"],
                    "img": data["item"]
                })
        raise ConfigImportError(str(E))
    except Exception as E:
        raise ConfigImportError(f"Login failed: {E}")

    # load remaining configuration items from the server
    cli.config.import_config_from_server(config, login, False)
