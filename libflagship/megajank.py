import Cryptodome.Util.Padding
import Cryptodome.Cipher.AES
import tinyec.registry
import tinyec.ec

from libflagship.util import b64e


# mqtt aes handling

def aes_cbc_encrypt(msg, key, iv):
    aes = Cryptodome.Cipher.AES.new(key=key, iv=iv, mode=Cryptodome.Cipher.AES.MODE_CBC)
    pmsg = Cryptodome.Util.Padding.pad(msg, block_size=16)
    cmsg = aes.encrypt(pmsg)
    return cmsg


def aes_cbc_decrypt(cmsg, key, iv):
    aes = Cryptodome.Cipher.AES.new(key=key, iv=iv, mode=Cryptodome.Cipher.AES.MODE_CBC)
    pmsg = aes.decrypt(cmsg)
    msg = Cryptodome.Util.Padding.unpad(pmsg, block_size=16)
    return msg


def mqtt_aes_encrypt(msg, key, iv=b"3DPrintAnkerMake"):
    return aes_cbc_encrypt(msg, key, iv)


def mqtt_aes_decrypt(cmsg, key, iv=b"3DPrintAnkerMake"):
    return aes_cbc_decrypt(cmsg, key, iv)


# mqtt checksum handling

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


# Elliptic-Curve Diffie-Hellman (ECDH) for password exchange in login api

anker_ec_v1_curve = tinyec.registry.get_curve("secp256r1")

anker_ec_v1_public_key = tinyec.ec.Keypair(anker_ec_v1_curve, pub=tinyec.ec.Point(
    anker_ec_v1_curve,
    0xC5C00C4F8D1197CC7C3167C52BF7ACB054D722F0EF08DCD7E0883236E0D72A38,
    0x68D9750CB47FA4619248F3D83F0F662671DADC6E2D31C2F41DB0161651C7C076
))


def ec_pubkey_export(key):
    return f"04{key.x:064x}{key.y:064x}"


def ecdh_encrypt_login_password(password, partner=anker_ec_v1_public_key):
    # make fresh EC key
    eckey = tinyec.ec.make_keypair(anker_ec_v1_curve)

    # Create ECDH instance for new key
    ecdh = tinyec.ec.ECDH(eckey)

    # Perform ECDH with partner key
    secret = ecdh.get_secret(partner)

    # Extract result as hex, use as AES key
    key = bytes.fromhex(hex(secret.x)[2:].zfill(64))

    # AES IV is just the first half of the key
    iv = key[:16]

    # Encrypt password with AES, return base64 encoding
    return ec_pubkey_export(eckey.pub), b64e(aes_cbc_encrypt(password, key, iv))


# pppp init string decoder

def pppp_decode_initstring_raw(input):
    shuffle = [0x49, 0x59, 0x43, 0x3d, 0xb5, 0xbf, 0x6d, 0xa3, 0x47, 0x53,
               0x4f, 0x61, 0x65, 0xe3, 0x71, 0xe9, 0x67, 0x7f, 0x02, 0x03,
               0x0b, 0xad, 0xb3, 0x89, 0x2b, 0x2f, 0x35, 0xc1, 0x6b, 0x8b,
               0x95, 0x97, 0x11, 0xe5, 0xa7, 0x0d, 0xef, 0xf1, 0x05, 0x07,
               0x83, 0xfb, 0x9d, 0x3b, 0xc5, 0xc7, 0x13, 0x17, 0x1d, 0x1f,
               0x25, 0x29, 0xd3, 0xdf]

    olen = len(input) >> 1

    q = 0
    output = [0] * olen

    for q in range(olen):
        xor = 0x39 ^ shuffle[q % 0x36]

        for p in range(q+1):
            xor ^= output[p]

        l = input[q*2+1] - 0x41
        h = input[q*2+0] - 0x41
        output[q] = xor ^ (l + (h << 4))

    return bytes(output)


def pppp_decode_initstring(input):
    res = pppp_decode_initstring_raw(input.encode())
    return res.decode().rstrip(",").split(",")


# pppp crypto curses

PPPP_SEED = "EUPRAKM"

PPPP_SHUFFLE = [
    [0x95, 0xe5, 0x61, 0x97, 0x83, 0x0d, 0xa7, 0xf1],
    [0xd3, 0x05, 0x95, 0x8b, 0xdf, 0x13, 0x6d, 0xef],
    [0x07, 0x61, 0x0d, 0x6d, 0x7f, 0x67, 0x17, 0x2b],
    [0xc1, 0xb5, 0x13, 0x0b, 0xdf, 0x8b, 0x49, 0x3b],
    [0x7f, 0x07, 0xd3, 0x02, 0x6d, 0x2f, 0x13, 0xc5],
    [0x6d, 0x3d, 0xfb, 0x0d, 0x0b, 0x29, 0xe9, 0x4f],
    [0x89, 0x2f, 0xe3, 0xe9, 0x0d, 0x83, 0x6d, 0xe5],
    [0x07, 0x53, 0x8b, 0x25, 0x95, 0x47, 0x1f, 0x29],
]


def crypto_decurse(input, key, shuffle):

    a, b, c, d = (1, 3, 5, 7)

    for q in key:
        q = ord(q)
        a, b, c, d = [
            shuffle[b + (q % a) & 7][q + (c % d) & 7],
            shuffle[c + (q % b) & 7][q + (d % a) & 7],
            shuffle[d + (q % c) & 7][q + (a % b) & 7],
            shuffle[a + (q % d) & 7][q + (b % c) & 7],
        ]

    output = [0] * len(input)
    for p, x in enumerate(input):
        output[p] = x ^ (a ^ b ^ c ^ d)

        a, b, c, d = [
            shuffle[b + (x % a) & 7][x + (c % d) & 7],
            shuffle[c + (x % b) & 7][x + (d % a) & 7],
            shuffle[d + (x % c) & 7][x + (a % b) & 7],
            shuffle[a + (x % d) & 7][x + (b % c) & 7],
        ]

    return output


def crypto_curse(input, key, shuffle):

    a, b, c, d = (1, 3, 5, 7)

    for q in key:
        q = ord(q)
        a, b, c, d = [
            shuffle[b + (q % a) & 7][q + (c % d) & 7],
            shuffle[c + (q % b) & 7][q + (d % a) & 7],
            shuffle[d + (q % c) & 7][q + (a % b) & 7],
            shuffle[a + (q % d) & 7][q + (b % c) & 7],
        ]

    output = [0] * (len(input) + 4)
    for p, x in enumerate(input):
        x = output[p] = x ^ (a ^ b ^ c ^ d)

        a, b, c, d = [
            shuffle[b + (x % a) & 7][x + (c % d) & 7],
            shuffle[c + (x % b) & 7][x + (d % a) & 7],
            shuffle[d + (x % c) & 7][x + (a % b) & 7],
            shuffle[a + (x % d) & 7][x + (b % c) & 7],
        ]

    for p in range(len(input), len(input)+4):
        x = output[p] = a ^ b ^ c ^ d ^ 0x43

        a, b, c, d = [
            shuffle[b + (x % a) & 7][x + (c % d) & 7],
            shuffle[c + (x % b) & 7][x + (d % a) & 7],
            shuffle[d + (x % c) & 7][x + (a % b) & 7],
            shuffle[a + (x % d) & 7][x + (b % c) & 7],
        ]

    return output


def crypto_decurse_string(input):

    output = crypto_decurse(input, key=PPPP_SEED, shuffle=PPPP_SHUFFLE)

    if output[-4:] != [0x43, 0x43, 0x43, 0x43]:
        raise ValueError("Invalid decode")

    return bytes(output[:-4])


def crypto_curse_string(input):

    output = crypto_curse(input, key=PPPP_SEED, shuffle=PPPP_SHUFFLE)

    return bytes(output)


# pppp crypto curse, older(?) version
#
# the simple_* functions have been adapted from https://github.com/fbertone/lib32100/issues/7
#

PPPP_SIMPLE_SEED = b"SSD@cs2-network."

PPPP_SIMPLE_SHUFFLE = [
    0x7C, 0x9C, 0xE8, 0x4A, 0x13, 0xDE, 0xDC, 0xB2, 0x2F, 0x21, 0x23, 0xE4, 0x30, 0x7B, 0x3D, 0x8C,
    0xBC, 0x0B, 0x27, 0x0C, 0x3C, 0xF7, 0x9A, 0xE7, 0x08, 0x71, 0x96, 0x00, 0x97, 0x85, 0xEF, 0xC1,
    0x1F, 0xC4, 0xDB, 0xA1, 0xC2, 0xEB, 0xD9, 0x01, 0xFA, 0xBA, 0x3B, 0x05, 0xB8, 0x15, 0x87, 0x83,
    0x28, 0x72, 0xD1, 0x8B, 0x5A, 0xD6, 0xDA, 0x93, 0x58, 0xFE, 0xAA, 0xCC, 0x6E, 0x1B, 0xF0, 0xA3,
    0x88, 0xAB, 0x43, 0xC0, 0x0D, 0xB5, 0x45, 0x38, 0x4F, 0x50, 0x22, 0x66, 0x20, 0x7F, 0x07, 0x5B,
    0x14, 0x98, 0x1D, 0x9B, 0xA7, 0x2A, 0xB9, 0xA8, 0xCB, 0xF1, 0xFC, 0x49, 0x47, 0x06, 0x3E, 0xB1,
    0x0E, 0x04, 0x3A, 0x94, 0x5E, 0xEE, 0x54, 0x11, 0x34, 0xDD, 0x4D, 0xF9, 0xEC, 0xC7, 0xC9, 0xE3,
    0x78, 0x1A, 0x6F, 0x70, 0x6B, 0xA4, 0xBD, 0xA9, 0x5D, 0xD5, 0xF8, 0xE5, 0xBB, 0x26, 0xAF, 0x42,
    0x37, 0xD8, 0xE1, 0x02, 0x0A, 0xAE, 0x5F, 0x1C, 0xC5, 0x73, 0x09, 0x4E, 0x69, 0x24, 0x90, 0x6D,
    0x12, 0xB3, 0x19, 0xAD, 0x74, 0x8A, 0x29, 0x40, 0xF5, 0x2D, 0xBE, 0xA5, 0x59, 0xE0, 0xF4, 0x79,
    0xD2, 0x4B, 0xCE, 0x89, 0x82, 0x48, 0x84, 0x25, 0xC6, 0x91, 0x2B, 0xA2, 0xFB, 0x8F, 0xE9, 0xA6,
    0xB0, 0x9E, 0x3F, 0x65, 0xF6, 0x03, 0x31, 0x2E, 0xAC, 0x0F, 0x95, 0x2C, 0x5C, 0xED, 0x39, 0xB7,
    0x33, 0x6C, 0x56, 0x7E, 0xB4, 0xA0, 0xFD, 0x7A, 0x81, 0x53, 0x51, 0x86, 0x8D, 0x9F, 0x77, 0xFF,
    0x6A, 0x80, 0xDF, 0xE2, 0xBF, 0x10, 0xD7, 0x75, 0x64, 0x57, 0x76, 0xF3, 0x55, 0xCD, 0xD0, 0xC8,
    0x18, 0xE6, 0x36, 0x41, 0x62, 0xCF, 0x99, 0xF2, 0x32, 0x4C, 0x67, 0x60, 0x61, 0x92, 0xCA, 0xD3,
    0xEA, 0x63, 0x7D, 0x16, 0xB6, 0x8E, 0xD4, 0x68, 0x35, 0xC3, 0x52, 0x9D, 0x46, 0x44, 0x1E, 0x17,
]


def simple_hash(seed):
    hash = [0] * 4

    for i in range(len(seed)):
        hash[0] = hash[0] ^ seed[i]
        hash[1] = hash[1] + seed[i] // 3
        hash[2] = hash[2] - seed[i]
        hash[3] = hash[3] + seed[i]

    return hash[::-1]


def _lookup(hash, b):
    index = hash[b & 0x3] + b
    return PPPP_SIMPLE_SHUFFLE[index % len(PPPP_SIMPLE_SHUFFLE)]


def simple_decrypt(seed, input):
    hash = simple_hash(seed)
    output = [0] * len(input)

    output[0] = input[0] ^ _lookup(hash, 0)
    for i in range(1, len(input)):
        output[i] = input[i] ^ _lookup(hash, input[i-1])

    return bytes(output)


def simple_encrypt(seed, input):
    hash = simple_hash(seed)
    output = [0] * len(input)

    output[0] = input[0] ^ _lookup(hash, 0)
    for i in range(1, len(input)):
        output[i] = input[i] ^ _lookup(hash, output[i-1])

    return bytes(output)


def simple_decrypt_string(input):
    return simple_decrypt(PPPP_SIMPLE_SEED, input)


def simple_encrypt_string(input):
    return simple_encrypt(PPPP_SIMPLE_SEED, input)


if __name__ == "__main__":
    print(simple_encrypt_string(b"foo"))
    print(simple_decrypt_string(simple_encrypt_string(b"foo")))
