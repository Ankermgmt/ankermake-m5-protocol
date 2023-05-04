import binascii
import crcmod
import struct


def enhex(s):
    return binascii.b2a_hex(s).decode()


def unhex(s):
    return binascii.a2b_hex(s)


def b64e(s):
    return binascii.b2a_base64(s).decode().strip()


def b64d(s):
    return binascii.a2b_base64(s)


def ppcs_crc16(data):
    crc16 = crcmod.mkCrcFun(0x11021, rev=False, initCrc=0x0000, xorOut=0x0000)
    return struct.pack("<H", crc16(data))
