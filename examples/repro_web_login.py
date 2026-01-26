#!/usr/bin/env python3
import json
import sys
import logging
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from libflagship.weblogin import login_web, WebLoginError

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("repro_web_login")

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

    log.info(f"Attempting WEB login for {email} (Region: {region})...")

    try:
        result = login_web(
            email=email,
            password=password,
            region=region,
            verify=True
        )
        
        log.info("Web Login SUCCESS!")
        log.info(f"Auth Token: {result.get('auth_token')}")
        log.info(f"User ID: {result.get('user_id')}")
        log.info(f"Nick Name: {result.get('nick_name')}")
        
    except WebLoginError as e:
        log.error(f"Web Login FAILED: {e}")
    except Exception as e:
        log.exception(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
