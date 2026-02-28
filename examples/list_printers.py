#!/usr/bin/env python3
import sys
import logging
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from libflagship.weblogin import login_web
from libflagship.httpapi import AnkerHTTPAppApiV1

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("list_printers")

def main():
    accounts_path = Path("secrets/accounts.json")
    if not accounts_path.exists():
        log.error(f"accounts.json not found: {accounts_path}")
        return
    try:
        accounts = json.loads(accounts_path.read_text())
    except Exception as e:
        log.error(f"Failed to read accounts.json: {e}")
        return

    email = accounts.get("username")
    password = accounts.get("secret")
    if not email or not password:
        log.error("accounts.json must contain username and secret")
        return
    region = "eu"

    log.info(f"Logging in as {email}...")
    try:
        # 1. Login
        login_res = login_web(email=email, password=password, region=region)
        auth_token = login_res["auth_token"]
        user_id = login_res["user_id"]
        log.info(f"Login success! Token: {auth_token[:10]}...")

        # 2. List Printers
        api = AnkerHTTPAppApiV1(auth_token=auth_token, user_id=user_id, region=region)
        log.info("Querying printer list...")
        
        printers = api.query_fdm_list()
        
        if not printers:
            log.info("No printers found on this account.")
            return

        print(json.dumps(printers, indent=2))
        
        for p in printers:
            log.info(f"Found Printer: {p.get('station_name')} (SN: {p.get('station_sn')})")

    except Exception as e:
        log.error(f"Error: {e}")

if __name__ == "__main__":
    main()
