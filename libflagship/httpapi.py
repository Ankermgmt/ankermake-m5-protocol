import logging as log
import requests
import functools
import json
import hashlib
import time
import socket
from libflagship.megajank import ecdh_encrypt_login_password


class APIError(Exception):

    def __init__(self, *args, **kwargs):
        if "json" in kwargs:
            self.json = kwargs["json"]
            del kwargs["json"]
            args = list(args)
            args.append(self.json)
        else:
            self.json = None

        super().__init__(*args)


def require_auth_token(func):

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self._auth:
            raise APIError("Missing auth token")
        return func(self, *args, **kwargs)

    return wrapper


def unwrap_api(func):

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.scope:
            raise APIError("scope undefined")
        data = func(self, *args, **kwargs)
        if data.ok:
            jsn = data.json()
            log.debug(f"JSON result: {json.dumps(jsn, indent=4)}")
            if jsn["code"] == 0:
                data = jsn.get("data")
                return data
            else:
                raise APIError("API error", json=jsn)
        else:
            raise APIError(f"API request failed: {data.status_code} {data.reason}")

    return wrapper


class AnkerHTTPApi:

    scope = None
    hosts = {
        "eu": "make-app-eu.ankermake.com",
        "us": "make-app.ankermake.com",
    }

    def __init__(self, auth_token=None, user_id=None, verify=True, region=None, base_url=None):
        self._auth = auth_token
        self._user_id = user_id
        self._verify = verify
        if base_url:
            self._base = base_url
        else:
            if region in self.hosts:
                host = self.hosts[region]
            else:
                raise APIError("must specify either base_url or region {'eu', 'us'}")
            self._base = f"https://{host}"

    @classmethod
    def guess_region(cls):
        return _find_closest_host(cls.hosts)

    @unwrap_api
    def _get(self, url, headers=None):
        full_headers = {}
        if self._user_id:
            full_headers["Gtoken"] = hashlib.md5(self._user_id.encode("utf-8")).hexdigest()
        if headers:
            full_headers.update(headers)
        return requests.get(f"{self._base}{self.scope}{url}", headers=full_headers, verify=self._verify)

    @unwrap_api
    def _post(self, url, headers=None, data=None):
        full_headers = {}
        if self._user_id:
            full_headers["Gtoken"] = hashlib.md5(self._user_id.encode("utf-8")).hexdigest()
        if headers:
            full_headers.update(headers)
        return requests.post(f"{self._base}{self.scope}{url}", headers=full_headers, verify=self._verify, json=data)


class AnkerHTTPAppApiV1(AnkerHTTPApi):

    scope = "/v1/app"

    def get_app_version(self, app_name="Ankermake_Windows", app_version=1, model="-"):
        return self._post("/ota/get_app_version", data={
            "app_name": app_name,
            "app_version": app_version,
            "model": model
        })

    @require_auth_token
    def query_fdm_list(self):
        return self._post("/query_fdm_list", headers={"X-Auth-Token": self._auth})

    @require_auth_token
    def equipment_get_dsk_keys(self, station_sns, invalid_dsks=None):
        if invalid_dsks is None:
            invalid_dsks = {}
        return self._post("/equipment/get_dsk_keys", headers={"X-Auth-Token": self._auth}, data={
            "invalid_dsks": invalid_dsks,
            "station_sns": station_sns,
        })


class AnkerHTTPPassportApiV1(AnkerHTTPApi):

    scope = "/v1/passport"

    @require_auth_token
    def profile(self):
        return self._get("/profile", headers={"X-Auth-Token": self._auth})


class AnkerHTTPPassportApiV2(AnkerHTTPApi):

    scope = "/v2/passport"

    def login(self, email, password, captcha_id=None, captcha_answer=None):
        public_key, encryped_pwd = ecdh_encrypt_login_password(password.encode())
        headers = {
            "App_name": "anker_make",
            "App_version": "",
            "Model_type": "PC",
            "Os_type": "windows",
            "Os_version": "10sp1",
        }
        data = {
            "client_secret_info": {
                "public_key": public_key,
            },
            "email": email,
            "password": encryped_pwd,
        }
        if captcha_id is not None:
            data["captcha_id"] = captcha_id
        if captcha_answer is not None:
            data["answer"] = captcha_answer

        return self._post("/login", headers=headers, data=data)


class AnkerHTTPHubApiV1(AnkerHTTPApi):

    scope = "/v1/hub"

    def query_device_info(self, station_sn, check_code):
        return self._post("/query_device_info", data={
            "station_sn": station_sn,
            "check_code": check_code,
        })

    def ota_get_rom_version(self, printer_sn, check_code, device_type="V8111_Model", current_version_name="V1.0.5"):
        return self._post("/ota/get_rom_version", data={
            "sn": printer_sn,
            "check_code": check_code,
            "device_type": device_type,
            "current_version_name": current_version_name,
        })


class AnkerHTTPHubApiV2(AnkerHTTPApi):

    scope = "/v2/hub"

    def query_device_info(self, station_sn, sec_code, sec_ts):
        return self._post("/query_device_info", data={
            "station_sn": station_sn,
            "sec_code": sec_code,
            "sec_ts": sec_ts,
        })

    def ota_get_rom_version(self, printer_sn, sec_code, sec_ts, device_type="V8111", current_version_name="V1"):
        return self._post("/ota/get_rom_version", data={
            "sn": printer_sn,
            "sec_code": sec_code,
            "sec_ts": sec_ts,
            "device_type": device_type,
            "current_version_name": current_version_name,
        })

    def get_p2p_connectinfo(self, printer_sn, sec_code, sec_ts):
        return self._post("/get_p2p_connectinfo", data={
            "station_sn": printer_sn,
            "sec_code": sec_code,
            "sec_ts": sec_ts,
        })


def _find_closest_host(hosts):
    host_names = list(hosts.values())
    connect_times = [_measure_host_connect_time(h) for h in host_names]
    host_index = connect_times.index(min(connect_times))
    host_name = host_names[host_index]

    host_keys = list(hosts.keys())
    position = host_names.index(host_name)
    return host_keys[position]


def _measure_host_connect_time(host, port=443):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        time_before = time.time()
        s.connect((host, port))
        result = time.time() - time_before
    return result
