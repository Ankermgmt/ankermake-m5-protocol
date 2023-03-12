from libflagship.util import unhex, b64d
import Cryptodome.Cipher.AES

cachekey = unhex("1b55f97793d58864571e1055838cac97")

def decrypt(data, key=cachekey):
    raw = b64d(data)

    aes = Cryptodome.Cipher.AES.new(key=key, mode=Cryptodome.Cipher.AES.MODE_ECB)
    pmsg = aes.decrypt(raw)
    return pmsg.rstrip(b"\x00").decode()
