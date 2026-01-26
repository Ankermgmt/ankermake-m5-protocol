import base64
import json
import requests
from pathlib import Path
from Cryptodome.Cipher import AES
from Cryptodome.PublicKey import ECC
from Cryptodome.Util.Padding import pad

# Hardcoded server public key
SERVER_PUBLIC_KEY_HEX = "04c5c00c4f8d1197cc7c3167c52bf7acb054d722f0ef08dcd7e0883236e0d72a3868d9750cb47fa4619248f3d83f0f662671dadc6e2d31c2f41db0161651c7c076"

def encrypt_password(password, server_public_hex):
    server_point = ECC.EccPoint(int(server_public_hex[2:66], 16), int(server_public_hex[66:], 16), curve="P-256")
    keypair = ECC.generate(curve="P-256")
    shared_point = server_point * int(keypair.d)
    shared_key_bytes = int(shared_point.x).to_bytes(32, "big")
    iv = shared_key_bytes[:16]
    cipher = AES.new(key=shared_key_bytes, iv=iv, mode=AES.MODE_CBC)
    padded_password = pad(password.encode("utf-8"), block_size=16)
    encrypted_bytes = cipher.encrypt(padded_password)
    client_public_key = "04" + int(keypair.pointQ.x).to_bytes(32, "big").hex() + int(keypair.pointQ.y).to_bytes(32, "big").hex()
    return base64.b64encode(encrypted_bytes).decode("utf-8"), client_public_key

accounts_path = Path("secrets/accounts.json")
if not accounts_path.exists():
    raise SystemExit(f"accounts.json not found: {accounts_path}")
try:
    accounts = json.loads(accounts_path.read_text())
except Exception as exc:
    raise SystemExit(f"Failed to read accounts.json: {exc}")

email = accounts.get("username")
password = accounts.get("secret")
if not email or not password:
    raise SystemExit("accounts.json must contain username and secret")

encrypted_pw, client_public_key = encrypt_password(password, SERVER_PUBLIC_KEY_HEX)

payload = {
    "email": email,
    "password": encrypted_pw,
    "client_secret_info": {
        "public_key": client_public_key
    }
}

headers = {
    "Content-Type": "application/json",
    "App-Name": "makeitreal",
    "Model-Type": "PC",
}

url = "https://make-app-eu.ankermake.com/v2/passport/login"

print(f"Sending request to {url}...")
resp = requests.post(url, json=payload, headers=headers)
print(f"Status Code: {resp.status_code}")
print(f"Response: {resp.text}")
