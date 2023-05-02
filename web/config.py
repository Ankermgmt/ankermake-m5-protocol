import web.util

import libflagship.httpapi
import libflagship.logincache

import cli.util
import cli.config


def config_show(config):
    config_output = f'''<p>Account:</p><p>
        user_id:    {config.account.user_id[:10]}...[REDACTED] <br/>
        auth_token: {config.account.auth_token[:10]}...[REDACTED] <br/>
        email:      {config.account.email} <br/>
        region:     {config.account.region.upper()} </p
    '''
    config_output += '<p>Printers:</p><hr/>'
    for p in config.printers:
        config_output += f'''<p>
            duid:      {p.p2p_duid} <br/>
            sn:        {p.sn} <br/>
            ip:        {p.ip_addr} <br/>
            wifi_mac:  {cli.util.pretty_mac(p.wifi_mac)} <br/>
            api_hosts: {', '.join(p.api_hosts)} <br/>
            p2p_hosts: {', '.join(p.p2p_hosts)} <hr/></p>
        '''
    return config_output


def config_import(login_file, config):
    # extract auth token
    cache = libflagship.logincache.load(login_file.stream.read())["data"]
    auth_token = cache["auth_token"]

    # extract account region
    region = libflagship.logincache.guess_region(cache["ab_code"])

    try:
        newConfig = cli.config.load_config_from_api(auth_token, region, False)
    except libflagship.httpapi.APIError as E:
        message = f"Config import failed: {E} <br/> Auth token might be expired: make sure Ankermake Slicer can connect, then try again"
        return web.util.flash_redirect(message, 'danger')
    except Exception as E:
        message = f"Config import failed: {E}"
        return web.util.flash_redirect(message, 'danger')

    try:
        config.save("default", newConfig)
    except Exception as E:
        message = f"Config import failed: {E}"
        return web.util.flash_redirect(message, 'danger')
    message = "AnkerMake Login Configuration imported successfully! Reloading..."
    return web.util.flash_redirect(message, 'success')
