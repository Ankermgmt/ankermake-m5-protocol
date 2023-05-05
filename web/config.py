import libflagship.httpapi
import libflagship.logincache

import cli.util
import cli.config


class ConfigImportError(Exception):
    """Raised when there is an error with the config api"""


def config_show(config):
    config_output = f"""<p>Account:</p><p>
        user_id:    {config.account.user_id[:10]}...[REDACTED] <br/>
        auth_token: {config.account.auth_token[:10]}...[REDACTED] <br/>
        email:      {config.account.email} <br/>
        region:     {config.account.region.upper()} </p
    """
    config_output += "<p>Printers:</p><hr/>"
    for p in config.printers:
        config_output += f"""<p>
            duid:      {p.p2p_duid} <br/>
            sn:        {p.sn} <br/>
            ip:        {p.ip_addr} <br/>
            wifi_mac:  {cli.util.pretty_mac(p.wifi_mac)} <br/>
            api_hosts: {', '.join(p.api_hosts)} <br/>
            p2p_hosts: {', '.join(p.p2p_hosts)} <hr/></p>
        """
    return config_output


def config_import(login_file, config):
    # extract auth token
    cache = libflagship.logincache.load(login_file.stream.read())["data"]
    auth_token = cache["auth_token"]

    # extract account region
    region = libflagship.logincache.guess_region(cache["ab_code"])

    try:
        new_config = cli.config.load_config_from_api(auth_token, region, False)
    except libflagship.httpapi.APIError as err:
        raise ConfigImportError(
            f"Config import failed: {err}. Auth token might be expired: make sure Ankermake Slicer can connect, then try again")
    except Exception as err:
        raise ConfigImportError(f"Config import failed: {err}")

    try:
        config.save("default", new_config)
    except Exception as E:
        raise ConfigImportError(f"Config import failed: {E}")
    return new_config
