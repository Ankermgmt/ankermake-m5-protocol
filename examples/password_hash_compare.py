#!/usr/bin/env python3
import base64
import hashlib
import json
import sys
import unicodedata
import hmac
import os
import re
from pathlib import Path

from examples.decode_login_flow import cryptojs_decrypt


def b64_digest(algo, data):
    h = hashlib.new(algo)
    h.update(data)
    return base64.b64encode(h.digest()).decode("utf-8")


def hex_digest(algo, data):
    h = hashlib.new(algo)
    h.update(data)
    return h.hexdigest()


def variants(password):
    raw = password
    variants = [
        ("utf8", raw.encode("utf-8")),
        ("utf8_strip", raw.strip().encode("utf-8")),
        ("utf16le", raw.encode("utf-16le")),
        ("utf16le_strip", raw.strip().encode("utf-16le")),
    ]
    return variants


def main():
    if len(sys.argv) > 1:
        trace_path = sys.argv[1]
    else:
        trace_path = "tmp/login_request.full.json"

    try:
        trace_pw = json.load(open(trace_path))["password"]
    except Exception as exc:
        print(f"Failed to read trace password from {trace_path}: {exc}", file=sys.stderr)
        return 2

    pw = input("Password: ")
    email = input("Email (optional): ").strip()
    share_key = os.getenv("ANKER_SHARE_KEY", "").strip()
    client_secret_key = os.getenv("ANKER_CLIENT_SECRET_PUBLIC_KEY", "").strip()
    profile_root = os.getenv("ANKER_PROFILE_ROOT", "").strip()
    entry_id = os.getenv("ANKER_ENTRY_ID", "").strip()
    targets = {trace_pw}
    print(f"Trace hash: {trace_pw}")
    try:
        decoded = base64.b64decode(trace_pw, validate=True)
        print(f"Trace hash decoded length: {len(decoded)} bytes")
    except Exception:
        print("Trace hash decoded length: invalid base64")

    algos = ["sha256", "sha1", "md5"]
    matches = []

    combos = []
    combos.extend(variants(pw))
    combos.extend([
        ("utf8_nfkc", unicodedata.normalize("NFKC", pw).encode("utf-8")),
        ("utf8_nfc", unicodedata.normalize("NFC", pw).encode("utf-8")),
    ])
    if email:
        combos.extend([
            ("utf8_pw+email", (pw + email).encode("utf-8")),
            ("utf8_email+pw", (email + pw).encode("utf-8")),
            ("utf8_pw:email", (pw + ":" + email).encode("utf-8")),
            ("utf8_email:pw", (email + ":" + pw).encode("utf-8")),
            ("utf8_pw|email", (pw + "|" + email).encode("utf-8")),
            ("utf8_email|pw", (email + "|" + pw).encode("utf-8")),
            ("utf8_pw+email_lower", (pw + email.lower()).encode("utf-8")),
            ("utf8_email_lower+pw", (email.lower() + pw).encode("utf-8")),
        ])
    combos.extend([
        ("utf8_pw_lower", pw.lower().encode("utf-8")),
        ("utf8_pw_upper", pw.upper().encode("utf-8")),
    ])

    print("\nQuick compare (sha256_b64):")
    for label, data in combos:
        quick = b64_digest("sha256", data)
        print(f"- {label}: {quick}")
        if quick in targets:
            matches.append(("sha256_b64", label, quick))

    for label, data in combos:
        for algo in algos:
            b64 = b64_digest(algo, data)
            if b64 in targets:
                matches.append((f"{algo}_b64", label, b64))
            h = hex_digest(algo, data)
            if h in targets:
                matches.append((f"{algo}_hex", label, h))
            # b64 of hex string
            b64_hex = base64.b64encode(h.encode("utf-8")).decode("utf-8")
            if b64_hex in targets:
                matches.append((f"{algo}_hex_b64", label, b64_hex))

        # hash-of-hash variants
        md5_hex = hex_digest("md5", data)
        md5_raw = hashlib.md5(data).digest()
        sha256_md5_hex = b64_digest("sha256", md5_hex.encode("utf-8"))
        sha256_md5_raw = base64.b64encode(hashlib.sha256(md5_raw).digest()).decode("utf-8")
        if sha256_md5_hex in targets:
            matches.append(("sha256_b64(md5_hex)", label, sha256_md5_hex))
        if sha256_md5_raw in targets:
            matches.append(("sha256_b64(md5_raw)", label, sha256_md5_raw))

    # salted variants (simple)
    salts = ["anker", "ankermake", "eufymake", "makeitreal"]
    salts.extend([
        "ff7c6c8fb3ced4ffdecb077e9c2dd96d",
        "2d0b871fcc61cf480917e28b39b6eda4",
        "ff7c6c8fb3ced4ffdecb077e9c2dd96dVLnZd6hxIluly0+5F9o4NiOrGCqFIGBstrL/eUJT7ewp27bvKA+Qa3hcUL9cnLd1OrrZnSAaR6zWQA8R+1Wu+g==",
        "2d0b871fcc61cf480917e28b39b6eda4pxos5B9AKU9IHxQA/QKBzKwNahImLAWSim0gzCCbsmPwPynXpyO65byMFQuzTK/tjdj7u+tCVqRUTc+wk1JFfg==",
        "7uJ2pCUU57A=",
        "1FCAFFBA5D13D4838BE780492C30821A",
        "H4sIAAAAAAAAAK1WW2/iOBT+K5VfN0Zx7rDaB8pliqZ02ELL7O6MKpOcpFYdG9kOLar47ysnKYVu2c5I0wfUc853vnO1nWc0GsxR7xmNnlJeZTB6MqAE5QMpclZMMj0Rl7JAPaMqcFCjvZTFgqoCDOohyAq404auOKCdg0ZZAQ3Ics4UaFAbGCq5HuU5pGZGt1zSzBozpq3XGKipFGjU++cdPPruoJQzEGbMuAFlHUsmbkFpJgXqIRJ4Hbfjh92wE/rIQSV9OjQG1hglbsdFu52DZpQJ8yXPNZiFokJzapgUY6kGslxLzQxkH2T4McGvSTl6SfmCmQVocy5VBuqaZqzSY6nmhqYPTBQDKQw8fdDWH6L4RWl7bdqPG29ORbaSTyeSmmjJqYEWBNkkV7QEjb7vHLRkmbnvi+wCWHFv+rreC2HqXveNUWxVGdBfxBVoA9l8U/x//T9NVydhV3kJq2uTnqKtjTeirAwsFE0f9PIexIymD2D6SrFNW82wdWUc5lttoOynKWg9uIf0gTNtTtC/xQ+ZgtRItZ0YUHXu51w2DDVVk7SwNMtbr59lzGIonylp3T8zziFbAIcSjNraoCDexiz1Ela3DB4/9rfR/ryZDCzRmtrZGVCW5BkJWgLqofSeCgEcOWhDeWU1Y7Rz9mZYy/T+wOi7zd8hRoGxp6xkpr5h7qS4e2QK7gwrQVbmrmScMw2pFJk+oPIsi03wywaUYhmMNiCMPlVzY+1zLh8v7Ty+OycqaqEvrDX4NeqUpUpqmZvOElbnSj5qUJ2Zkkauqrxz83naacY5UzJnHBzXIeHvP+BkqNGdS1nMDVXGcZ3gZ5zsvcTBQO3XNGU/w5lcz6k1179MFKcaNJYqhb3bHu2gUtu3ALS5ESyXqhwy3RwnJsUF00YWipan+1koWa29fRpHEzxcgwxyWnHzycLfQx+Bq4fyJOXhTuzzO7kXr4hPcmNfRZHCRwuy9/lwSQZyzbg0U5lBpzm2mUMch/hxEPgkCrxuVA+svYrGTGlzXYnX13VUrs32fdN/qwHIVYpqtjkU5cv1Z8HT/qTPOeqhnHJtO7Zcjo4VOl3nldW49f9FRVX2ImzsU+E6aOpH4UAqOPasHxdh5qA2LAX9Jg6svi6OVedMFMcaW+CxZt/CG21jt3r7VALN6oE8o9GCFqiHviH2G80ienN+OzqfX95OVtuLz1dlRq+Hy4vplevS7sC/ir4O/qZ/9f/4hmy8pzWre4amUjhnLjkbQnrmuV545sY9l/Q87+zTdFHXVgmjtgOZ2cEOR8hB9thVutXUt9DLN9Nk2ORlP7bQDF9j4iZeGLuYYEKcGR7iwPOTBHs4QsefUQ06Jl0v8rCPI6eV49i1criXwzB+lX0SBgnBBCeNHHVDP/RxgONWjknXP+ALA0JigiPcbWUv8VwX+zio5SgJ4gB3MfEa0Y1IjBPskVoMQj/2cYKThiyIvCjEoYcJ8dD729u2IA6TKMQBTtDbtWwAQey7JHqtgoTdbhJi8lIlIX6XhNgLmyZaym7i+wEmbV1R5MYJJtjfS/HeO3KTxMMENyUFvpu89jPw4sCyeGi3+xfX4GQBIwsAAA=="
    ])
    if email:
        salts.extend([email, email.lower(), email.upper()])
    if share_key:
        salts.append(share_key)
    if client_secret_key:
        salts.append(client_secret_key)
    for salt in salts:
        for label, data in combos:
            b64 = b64_digest("sha256", data + salt.encode("utf-8"))
            if b64 in targets:
                matches.append(("sha256_b64(+salt)", f"{label}+{salt}", b64))
            b64 = b64_digest("sha256", salt.encode("utf-8") + data)
            if b64 in targets:
                matches.append(("sha256_b64(salt+)", f"{salt}+{label}", b64))

    # HMAC variants
    keys = ["anker", "ankermake", "eufymake"]
    if email:
        keys.extend([email, email.lower(), email.upper()])
    if share_key:
        keys.append(share_key)
        try:
            keys.append(bytes.fromhex(share_key))
        except Exception:
            pass
    if client_secret_key:
        keys.append(client_secret_key)
        try:
            keys.append(bytes.fromhex(client_secret_key))
        except Exception:
            pass
    for key in keys:
        for label, data in combos:
            if isinstance(key, bytes):
                key_bytes = key
                key_label = "hex"
            else:
                key_bytes = key.encode("utf-8")
                key_label = "utf8"
            h = hmac.new(key_bytes, data, hashlib.sha256).digest()
            b64 = base64.b64encode(h).decode("utf-8")
            if b64 in targets:
                matches.append(("hmac_sha256_b64", f"key({key_label})={key} {label}", b64))

    # PBKDF2 variants (common iteration counts)
    pbk_iters = [1000, 2000, 4096, 10000]
    pbk_salts = ["anker", "ankermake", "eufymake"]
    if email:
        pbk_salts.extend([email, email.lower()])
    if share_key:
        pbk_salts.append(share_key)
        try:
            pbk_salts.append(bytes.fromhex(share_key))
        except Exception:
            pass
    if client_secret_key:
        pbk_salts.append(client_secret_key)
        try:
            pbk_salts.append(bytes.fromhex(client_secret_key))
        except Exception:
            pass
    for salt in pbk_salts:
        for label, data in combos:
            for iters in pbk_iters:
                if isinstance(salt, bytes):
                    salt_bytes = salt
                    salt_label = "hex"
                else:
                    salt_bytes = salt.encode("utf-8")
                    salt_label = "utf8"
                dk = hashlib.pbkdf2_hmac("sha256", data, salt_bytes, iters, dklen=32)
                b64 = base64.b64encode(dk).decode("utf-8")
                if b64 in targets:
                    matches.append((f"pbkdf2_sha256_b64_{iters}", f"{label} salt({salt_label})={salt}", b64))

    # Try to derive share_key from profile if requested
    if not share_key and profile_root and entry_id:
        log_dir = Path(profile_root) / "Default" / "IndexedDB"
        if log_dir.exists():
            logs = list(log_dir.rglob("*.log"))
            for path in logs:
                try:
                    content = path.read_bytes()
                except Exception:
                    continue
                for token in re.findall(rb"U2FsdGVkX1[0-9A-Za-z+/=]{20,}", content):
                    try:
                        dec = cryptojs_decrypt(token.decode(), "anker-make-secret-key")
                    except Exception:
                        continue
                    if not dec:
                        continue
                    try:
                        obj = json.loads(dec)
                    except Exception:
                        continue
                    if isinstance(obj, dict) and obj.get("entryId") == entry_id:
                        share_key = obj.get("shareKey", "")
                        print(f"Derived share key from profile: {share_key}")
                        break
                if share_key:
                    break

    if matches:
        print("MATCHES:")
        for algo, label, value in matches:
            print(f"- {algo} ({label}): {value}")
        return 0

    print("No matches found with common variants.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
