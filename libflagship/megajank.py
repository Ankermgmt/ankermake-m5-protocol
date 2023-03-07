import Cryptodome.Util.Padding
import Cryptodome.Cipher.AES

def mqtt_aes_encrypt(msg, key, iv=b"3DPrintAnkerMake"):
    aes = Cryptodome.Cipher.AES.new(key=key, iv=iv, mode=Cryptodome.Cipher.AES.MODE_CBC)
    pmsg = Cryptodome.Util.Padding.pad(msg, block_size=16)
    cmsg = aes.encrypt(pmsg)
    return cmsg

def mqtt_aes_decrypt(cmsg, key, iv=b"3DPrintAnkerMake"):
    aes = Cryptodome.Cipher.AES.new(key=key, iv=iv, mode=Cryptodome.Cipher.AES.MODE_CBC)
    pmsg = aes.decrypt(cmsg)
    msg = Cryptodome.Util.Padding.unpad(pmsg, block_size=16)
    return msg

def mqtt_checksum_remove(payload):
    if xor_bytes(payload) != 0:
        # raise ...
        print(f"MALFORMED MESSAGE: {payload}")
    return payload[:-1]

def mqtt_checksum_add(msg):
    return msg + bytes([xor_bytes(msg)])

def xor_bytes(data):
    s = 0
    for x in data:
        s ^= x
    return s
