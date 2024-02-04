import logging as log
import contextlib
import json
from datetime import datetime

from pathlib import Path
from platformdirs import PlatformDirs

from libflagship.megajank import pppp_decode_initstring
from libflagship.httpapi import AnkerHTTPAppApiV1, AnkerHTTPPassportApiV1
from libflagship.util import unhex

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
        if write and pr is not None:
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


def update_printer_ip_addresses(config, printer_ips: list) -> list:
    """
    Checks configured printer IP addresses against the given set of addresses
    and updates the IP address in the configuration if they differ.

    Returns:
    - List of names of updated printers, None upon an error
    """
    updated_printers = list()

    with config.modify() as cfg:
        if not cfg or not cfg.printers:
            log.error("No printers configured. Run 'config login' or 'config import' to populate.")
            return None

        for p in cfg.printers:
            prefix = f"  Printer [{p.p2p_duid}]:"
            if p.p2p_duid in printer_ips:
                if p.ip_addr != printer_ips[p.p2p_duid]:
                    old_ip = p.ip_addr if p.ip_addr else "<empty>"
                    log.info(f"{prefix} Updating IP address from {old_ip} to {printer_ips[p.p2p_duid]}")
                    p.ip_addr = printer_ips[p.p2p_duid]
                    updated_printers.append(p.name)
                else:
                    log.info(f"{prefix} IP address {p.ip_addr} is already up-to-date")
            else:
                log.warning(f"{prefix} No network response received, check connection!")

    return updated_printers


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
