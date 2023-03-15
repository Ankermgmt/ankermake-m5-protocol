import requests
import functools
import json
import hashlib

def require_auth_token(func):

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self._auth:
            raise ValueError("Missing auth token")
        return func(self, *args, **kwargs)

    return wrapper

def unwrap_api(func):

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.scope:
            raise ValueError("scope undefined")
        data = func(self, *args, **kwargs)
        if data.ok:
            json = data.json()
            if json["code"] == 0:
                return json.get("data")
            else:
                raise ValueError(f"API error", json)
        else:
            raise ValueError(f"API request failed: {data.status_code} {data.reason}")

    return wrapper

class AnkerHTTPApi:

    scope = None

    def __init__(self, auth_token=None, verify=True, region=None, base_url=None):
        self._auth = auth_token
        self._verify = verify
        if base_url:
            self._base = base_url
        else:
            if region == "eu":
                self._base = "https://make-app-eu.ankermake.com"
            elif region == "us":
                self._base = "https://make-app.ankermake.com"
            else:
                raise ValueError("must specify either base_url or region {'eu', 'us'}")

    @staticmethod
    def calc_check_code(sn, mac):
        input = f"{sn}+{sn[-4:]}+{mac}"
        return hashlib.md5(input.encode()).hexdigest()

    @unwrap_api
    def _get(self, url, headers=None):
        return requests.get(f"{self._base}{self.scope}{url}", headers=headers, verify=self._verify)

    @unwrap_api
    def _post(self, url, headers=None, data=None):
        return requests.post(f"{self._base}{self.scope}{url}", headers=headers, verify=self._verify, json=data)

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

class AnkerHTTPPassportApiV1(AnkerHTTPApi):

    scope = "/v1/passport"

    @require_auth_token
    def profile(self):
        return self._get("/profile", headers={"X-Auth-Token": self._auth})

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
