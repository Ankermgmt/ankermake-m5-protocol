import binascii

def enhex(s):
    return binascii.b2a_hex(s).decode()

def unhex(s):
    return binascii.a2b_hex(s)

def b64e(s):
    return binascii.b2a_base64(s).decode().strip()
