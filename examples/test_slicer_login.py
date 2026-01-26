import sys
import os
import json
from pathlib import Path
sys.path.append(os.getcwd())
import libflagship.weblogin
import logging

# setup logging to see what's happening
logging.basicConfig(level=logging.DEBUG)

accounts_path = Path("secrets/accounts.json")
if not accounts_path.exists():
    print(f"accounts.json not found: {accounts_path}")
    raise SystemExit(1)
try:
    accounts = json.loads(accounts_path.read_text())
except Exception as e:
    print(f"Failed to read accounts.json: {e}")
    raise SystemExit(1)

email = accounts.get("username")
password = accounts.get("secret")
if not email or not password:
    print("accounts.json must contain username and secret")
    raise SystemExit(1)

try:
    print(f"Testing Slicer login for {email}...")
    res = libflagship.weblogin.login_email_password(email, password, region="eu")
    print("SUCCESS!")
    print(res)
except Exception as e:
    print(f"FAILED: {e}")
