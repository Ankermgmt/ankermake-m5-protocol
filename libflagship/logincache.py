from libflagship.util import unhex, b64d
import Cryptodome.Cipher.AES
import json

cachekey = unhex("1b55f97793d58864571e1055838cac97")


def guess_region(cc):
    us_regions = {"US", "CA", "MX", "BR", "AR", "CU", "BS", "AU", "NZ"}
    if cc in us_regions:
        return "us"
    else:
        return "eu"


def decrypt(data, key=cachekey):
    raw = b64d(data)

    aes = Cryptodome.Cipher.AES.new(key=key, mode=Cryptodome.Cipher.AES.MODE_ECB)
    pmsg = aes.decrypt(raw)
    return pmsg.rstrip(b"\x00").decode()


def load(data, key=cachekey):
    try:
        raw = decrypt(data, key)
    except Exception:
        # older versions of the Ankermake slicer just save unencrypted login
        # credentials in login, so attempt to decode the file contents as-is
        raw = data

    return json.loads(raw.strip())
