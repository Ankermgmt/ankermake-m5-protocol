#!/usr/bin/env python3
import json
import os
import sys

import requests

from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from libflagship.megajank import ecdh_encrypt_login_password


HOSTS = {
    "eu": "make-app-eu.ankermake.com",
    "us": "make-app.ankermake.com",
}


def main():
    accounts_path = Path(os.getenv("ANKER_ACCOUNTS_JSON", "secrets/accounts.json"))
    if not accounts_path.exists():
        print(f"accounts.json not found at {accounts_path}", file=sys.stderr)
        return 2

    try:
        accounts = json.loads(accounts_path.read_text())
    except Exception as exc:
        print(f"Failed to read accounts.json: {exc}", file=sys.stderr)
        return 2

    email = accounts.get("username")
    password = accounts.get("secret")
    if not email or not password:
        print("accounts.json must contain username and secret", file=sys.stderr)
        return 2

    region = os.getenv("ANKER_REGION", "eu").lower()
    host = HOSTS.get(region)
    if not host:
        print(f"Invalid ANKER_REGION '{region}', expected eu/us", file=sys.stderr)
        return 2

    captcha_id = os.getenv("ANKER_CAPTCHA_ID", "").strip()
    captcha_answer = os.getenv("ANKER_CAPTCHA_ANSWER", "").strip()

    public_key, encrypted_pwd = ecdh_encrypt_login_password(password.encode("utf-8"))

    data = {
        "client_secret_info": {"public_key": public_key},
        "email": email,
        "password": encrypted_pwd,
    }
    if captcha_id:
        data["captcha_id"] = captcha_id
    if captcha_answer:
        data["answer"] = captcha_answer

    headers = {
        "App_name": "anker_make",
        "App_version": "",
        "Model_type": "PC",
        "Os_type": "windows",
        "Os_version": "10sp1",
    }

    url = f"https://{host}/v2/passport/login"
    resp = requests.post(url, headers=headers, json=data, timeout=20)

    print(f"HTTP {resp.status_code}")
    try:
        jsn = resp.json()
    except Exception:
        text = resp.text
        print(text[:1000])
        return 1

    # Avoid dumping sensitive fields
    if "data" in jsn and isinstance(jsn["data"], dict):
        jsn["data"].pop("auth_token", None)
        jsn["data"].pop("user_id", None)
    print(json.dumps(jsn, indent=2))

    if jsn.get("code") == 0:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
