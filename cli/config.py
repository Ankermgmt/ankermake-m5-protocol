import logging as log
import contextlib
import json
from datetime import datetime

from pathlib import Path
from platformdirs import PlatformDirs

from libflagship.megajank import pppp_decode_initstring
from libflagship.httpapi import AnkerHTTPApi, AnkerHTTPAppApiV1, \
                                AnkerHTTPPassportApiV1, AnkerHTTPPassportApiV2, \
                                APIError
from libflagship.util import unhex
from libflagship import logincache

from .model import Serialize, Account, Printer, Config


class BaseConfigManager:

    def __init__(self, dirs: PlatformDirs, classes=None):
        self._dirs = dirs
        if classes:
            self._classes = {t.__name__: t for t in classes}
        else:
            self._classes = []
        dirs.user_config_path.mkdir(exist_ok=True, parents=True)

    @contextlib.contextmanager
    def _borrow(self, value, write, default=None):
        pr = self.load(value, default)
        yield pr
        if write:
            self.save(value, pr)

    @property
    def config_root(self):
        return self._dirs.user_config_path

    def config_path(self, name):
        return self.config_root / Path(f"{name}.json")

    def _load_json(self, val):
        if "__type__" not in val:
            return val

        typename = val["__type__"]
        if typename not in self._classes:
            return val

        return self._classes[typename].from_dict(val)

    @staticmethod
    def _save_json(val):
        if not isinstance(val, Serialize):
            return val

        data = val.to_dict()
        data["__type__"] = type(val).__name__
        return data

    def load(self, name, default):
        path = self.config_path(name)
        if not path.exists():
            return default

        return json.load(path.open(), object_hook=self._load_json)

    def save(self, name, value):
        path = self.config_path(name)
        path.write_text(json.dumps(value, default=self._save_json, indent=2) + "\n")


class AnkerConfigManager(BaseConfigManager):

    def modify(self):
        return self._borrow("default", write=True)

    def open(self):
        return self._borrow("default", write=False, default=Config(account=None, printers=[]))


def configmgr(profile="default"):
    return AnkerConfigManager(PlatformDirs("ankerctl"), classes=(Config, Account, Printer))


def load_config_from_api(auth_token, region, insecure):
    log.info("Initializing API..")
    appapi = AnkerHTTPAppApiV1(auth_token=auth_token, region=region, verify=not insecure)
    ppapi = AnkerHTTPPassportApiV1(auth_token=auth_token, region=region, verify=not insecure)

    # request profile and printer list
    log.info("Requesting profile data..")
    profile = ppapi.profile()

    # create config object
    config = Config(account=Account(
        auth_token=auth_token,
        region=region,
        user_id=profile['user_id'],
        email=profile["email"],
        country=profile["country"]["code"],
    ), printers=[])

    log.info("Requesting printer list..")
    printers = appapi.query_fdm_list()

    log.info("Requesting pppp keys..")
    sns = [pr["station_sn"] for pr in printers]
    dsks = {dsk["station_sn"]: dsk for dsk in appapi.equipment_get_dsk_keys(station_sns=sns)["dsk_keys"]}

    # populate config object with printer list
    # Sort the list of printers by printer.id
    printers.sort(key=lambda p: p["station_id"])
    for pr in printers:
        station_sn = pr["station_sn"]
        config.printers.append(Printer(
            id=pr["station_id"],
            sn=station_sn,
            name=pr["station_name"],
            model=pr["station_model"],
            create_time=datetime.fromtimestamp(pr["create_time"]),
            update_time=datetime.fromtimestamp(pr["update_time"]),
            mqtt_key=unhex(pr["secret_key"]),
            wifi_mac=pr["wifi_mac"],
            ip_addr=pr["ip_addr"],
            api_hosts=pppp_decode_initstring(pr["app_conn"]),
            p2p_hosts=pppp_decode_initstring(pr["p2p_conn"]),
            p2p_duid=pr["p2p_did"],
            p2p_key=dsks[pr["station_sn"]]["dsk_key"],
        ))
        log.info(f"Adding printer [{station_sn}]")

    return config


def fetch_config_by_login(email, password, region, insecure, captcha_id=None, captcha_answer=None):
    log.info("Initializing API..")
    if not region:
        region = AnkerHTTPApi.guess_region()
        log.info(f"Using region '{region.upper()}'")
    ppapi = AnkerHTTPPassportApiV2(region=region, verify=not insecure)

    log.info("Logging in..")
    login = ppapi.login(email, password, captcha_id=captcha_id, captcha_answer=captcha_answer)
    return login


def import_config_from_server(config, login_data, insecure):
    # extract auth token
    auth_token = login_data["auth_token"]

    # extract account region
    region = logincache.guess_region(login_data["ab_code"])

    try:
        cfg = load_config_from_api(auth_token, region, insecure)
    except APIError as E:
        log.critical(f"Config import failed: {E} "
                     "(auth token might be expired: make sure Ankermake Slicer can connect, then try again)")
    except Exception as E:
        log.critical(f"Config import failed: {E}")

    # prepare to rescue any printer IP addresses already configured
    printer_ips = get_printer_ips(config)

    # save config to json file named `ankerctl/default.json`
    config.save("default", cfg)

    # restore printer IP addresses
    update_empty_printer_ips(config, printer_ips)


def get_printer_ips(config):
    try:
        with config.open() as cfg:
            # prepare to rescue any printer IP addresses already configured
            printer_ips = dict([[p.sn, p.ip_addr] for p in cfg.printers if p.ip_addr])
    except KeyError:
        printer_ips = {}

    return printer_ips


def update_empty_printer_ips(config, printer_ips):
    with config.modify() as cfg:
        # update empty printer IP addresses to the provided ones
        for printer in cfg.printers:
            if not printer.ip_addr and printer.sn in printer_ips:
                log.debug(f"Updating IP address of printer [{printer.sn}] to {printer_ips[printer.sn]}")
                printer.ip_addr = printer_ips[printer.sn]


def attempt_config_upgrade(config, profile, insecure):
    path = config.config_path("default")
    data = json.load(path.open())
    cfg = load_config_from_api(
        data["account"]["auth_token"],
        data["account"]["region"],
        insecure
    )

    # save config to json file named `ankerctl/default.json`
    config.save("default", cfg)
    log.info("Finished import")
