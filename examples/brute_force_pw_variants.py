#!/usr/bin/env python3
import base64
import hashlib
import json
from pathlib import Path

def get_hash(pw):
    return base64.b64encode(hashlib.sha256(pw.encode("utf-8")).digest()).decode("utf-8")

def main():
    target = "8jkPbTHqgC5zIxvlDWNx55XKjaDq/aNhvdFLR5zRzvs="
    accounts_path = Path("secrets/accounts.json")
    if accounts_path.exists():
        try:
            accounts = json.loads(accounts_path.read_text())
            base_pw = accounts.get("secret", "")
        except Exception:
            base_pw = ""
    else:
        base_pw = ""
    if not base_pw:
        base_pw = input("Password (base for variants): ").strip()
    
    variants = [
        f"{base_pw} @s",
        base_pw,
        base_pw.replace("%%", "%"),  # collapse double percent
        base_pw.replace("%", "%%"),  # double percent
        base_pw.replace("%", "%25"),  # URL encoded %
        base_pw.replace("^", "%5E"),  # URL encoded ^
        base_pw.replace("%", "%25").replace("^", "%5E"),  # Fully URL encoded
    ]
    
    print(f"Target Captured Hash: {target}\n")
    
    for v in variants:
        h = get_hash(v)
        match = "MATCH!" if h == target else ""
        print(f"PW: {v:30} -> Hash: {h} {match}")

if __name__ == "__main__":
    main()
