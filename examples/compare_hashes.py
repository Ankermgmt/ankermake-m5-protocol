#!/usr/bin/env python3
import base64
import hashlib
import json
from pathlib import Path

def main():
    accounts_path = Path("secrets/accounts.json")
    if not accounts_path.exists():
        print(f"accounts.json not found: {accounts_path}")
        return
    try:
        accounts = json.loads(accounts_path.read_text())
    except Exception as e:
        print(f"Failed to read accounts.json: {e}")
        return
    password_plain = accounts.get("secret")
    if not password_plain:
        print("accounts.json must contain secret")
        return
    
    # Calculate SHA256 base64 hash (current logic)
    sha256_hash = base64.b64encode(hashlib.sha256(password_plain.encode("utf-8")).digest()).decode("utf-8")
    
    # Calculate MD5 hash (alternative)
    md5_hash = hashlib.md5(password_plain.encode("utf-8")).hexdigest()
    # Calculate SHA256 of MD5 (another common pattern)
    sha256_of_md5 = base64.b64encode(hashlib.sha256(md5_hash.encode("utf-8")).digest()).decode("utf-8")
    
    print(f"Plain Password: {password_plain}")
    print(f"SHA256 Hash (B64): {sha256_hash}")
    print(f"MD5 Hash: {md5_hash}")
    print(f"SHA256 of MD5 (B64): {sha256_of_md5}")

    creds_path = Path("tmp/credentials.json")
    if creds_path.exists():
        creds = json.loads(creds_path.read_text())
        captured_pw = creds.get("password")
        print(f"\nCaptured Password from mitm: {captured_pw}")
        
        if captured_pw == sha256_hash:
            print("MATCH found with SHA256!")
        elif captured_pw == sha256_of_md5:
            print("MATCH found with SHA256(MD5)!")
        else:
            print("NO MATCH found with standard hashes.")

if __name__ == "__main__":
    main()
