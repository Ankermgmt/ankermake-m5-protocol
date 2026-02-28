#!/usr/bin/env python3
import json
import sys
import logging
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from libflagship.weblogin import login_email_password, WebLoginError

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("repro_login")

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
    password_plain = accounts.get("secret")
    ab = "DE"
    ab_code = "DE"

    if not email or not password_plain:
        log.error("accounts.json must contain username and secret")
        return

    log.info(f"Attempting login for {email} (Region: {ab})...")

    # Debug callback to inspect the payload we are sending
    def debug_cb(info):
        if "request" in info:
            req = info["request"]
            # log.info(f"Sending Request to {req['url']}")
            # log.info(f"Payload: {json.dumps(req['payload'], indent=2)}")
        if "response" in info:
            resp = info["response"]
            log.info(f"Response Status: {resp['status']}")
            if resp.get("error_decrypted"):
                log.info(f"Decrypted Error: {resp['error_decrypted']}")

    try:
        # We assume 'password' from the capture IS the base64 encoded hash
        # So we pass it as password_b64. 
        # We provide a dummy "password" string because the function signature might require it 
        # (though looking at the code, it uses password only if password_b64 is None).
        
        result = login_email_password(
            email=email,
            password=password_plain, 
            password_b64=None,
            region="eu", 
            country="DE", 
            ab=ab,
            ab_code=ab_code,
            verify=True,
            debug_cb=debug_cb
        )
        
        log.info("Login SUCCESS!")
        log.info(f"Auth Token: {result.get('auth_token')}")
        log.info(f"User ID: {result.get('data', {}).get('user_id')}")
        log.info(f"Nickname: {result.get('data', {}).get('nick_name')}")
        
    except WebLoginError as e:
        log.error(f"Login FAILED: {e}")
    except Exception as e:
        log.exception(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
