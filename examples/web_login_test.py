import base64
import json
import requests
from pathlib import Path
from Cryptodome.Cipher import AES
from Cryptodome.PublicKey import ECC
from Cryptodome.Util.Padding import pad

# Hardcoded server public key from app.js (variable 's')
SERVER_PUBLIC_KEY_HEX = "04c5c00c4f8d1197cc7c3167c52bf7acb054d722f0ef08dcd7e0883236e0d72a3868d9750cb47fa4619248f3d83f0f662671dadc6e2d31c2f41db0161651c7c076"

def _parse_public_point(public_hex):
    if not public_hex.startswith("04") or len(public_hex) != 130:
        raise ValueError("Invalid public key format")
    x = int(public_hex[2:66], 16)
    y = int(public_hex[66:], 16)
    return ECC.EccPoint(x, y, curve="P-256")

def _export_public_key_hex(key):
    point = key.pointQ
    x = int(point.x).to_bytes(32, "big").hex()
    y = int(point.y).to_bytes(32, "big").hex()
    return f"04{x}{y}"

def encrypt_password(password, server_public_hex):
    # 1. Generate Local Keypair
    keypair = ECC.generate(curve="P-256")
    
    # 2. Derive Shared Secret
    server_point = _parse_public_point(server_public_hex)
    shared_point = server_point * int(keypair.d)
    # The JS uses the X coordinate as the shared key (usually 32 bytes)
    # _derive_share_key_hex in weblogin.py does this too.
    shared_key_bytes = int(shared_point.x).to_bytes(32, "big")
    
    # 3. Derive IV
    # JS: l=await p(a) -> p exports raw key and takes slice(0,16)
    # effectively IV is the first 16 bytes of the shared key
    iv = shared_key_bytes[:16]
    
    # 4. Encrypt
    cipher = AES.new(key=shared_key_bytes, iv=iv, mode=AES.MODE_CBC)
    padded_password = pad(password.encode("utf-8"), block_size=16)
    encrypted_bytes = cipher.encrypt(padded_password)
    
    # 5. Base64 encode
    # JS: (0,o.sM)(u) -> seems to be standard base64 from context
    encrypted_b64 = base64.b64encode(encrypted_bytes).decode("utf-8")
    
    return encrypted_b64, _export_public_key_hex(keypair)

def login(email, password):
    print(f"Attempting login for {email} with password length {len(password)}")
    
    encrypted_pw, client_public_key = encrypt_password(password, SERVER_PUBLIC_KEY_HEX)
    
    # "00"+t.toString(16)).substring(("00"+t.toString(16)).length-2) logic in JS for public key
    # My python _export_public_key_hex produces standard hex, which should match.
    
    # Payload structure from login.js
    payload = {
        "email": email,
        "password": encrypted_pw,
        "client_secret_info": {
            "public_key": client_public_key
        }
    }
    
    # Headers - mimicking the request from app.js / weblogin.py
    headers = {
        "Content-Type": "application/json",
        "App-Name": "makeitreal",
        "Model-Type": "WEB",
        # "X-Encryption-Info": "algo_ecdh" # Maybe needed?
    }
    
    url = "https://aiot-wapi-eu.ankermake.com/passport/login"
    
    print(f"Sending request to {url}")
    # print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        resp = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.text}")
        return resp.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
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
    base_pw = accounts.get("secret")
    if not email or not base_pw:
        print("accounts.json must contain username and secret")
        raise SystemExit(1)

    passwords = [
        base_pw,
    ]
    
    for pwd in passwords:
        print(f"\n--- Testing Password: {pwd} ---")
        res = login(email, pwd)
        if res and res.get("code") == 0: # Success usually code 0 or 200
            print("SUCCESS!")
            # Save token if successful?
            break
        else:
            print("Failed.")
