import Cryptodome.Util.Padding
import Cryptodome.Cipher.AES

## mqtt aes handling

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

## mqtt checksum handling

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

## pppp crypto curses

PPPP_SEED = "EUPRAKM"

PPPP_SHUFFLE = [
    [ 0x95, 0xe5, 0x61, 0x97, 0x83, 0x0d, 0xa7, 0xf1, ],
    [ 0xd3, 0x05, 0x95, 0x8b, 0xdf, 0x13, 0x6d, 0xef, ],
    [ 0x07, 0x61, 0x0d, 0x6d, 0x7f, 0x67, 0x17, 0x2b, ],
    [ 0xc1, 0xb5, 0x13, 0x0b, 0xdf, 0x8b, 0x49, 0x3b, ],
    [ 0x7f, 0x07, 0xd3, 0x02, 0x6d, 0x2f, 0x13, 0xc5, ],
    [ 0x6d, 0x3d, 0xfb, 0x0d, 0x0b, 0x29, 0xe9, 0x4f, ],
    [ 0x89, 0x2f, 0xe3, 0xe9, 0x0d, 0x83, 0x6d, 0xe5, ],
    [ 0x07, 0x53, 0x8b, 0x25, 0x95, 0x47, 0x1f, 0x29, ],
]

def crypto_decurse(input, key, shuffle):

    a, b, c, d = (1, 3, 5, 7)

    for q in key:
        q = ord(q)
        a, b, c, d = [
            shuffle[b + (q%a) & 7][q + (c%d) & 7],
            shuffle[c + (q%b) & 7][q + (d%a) & 7],
            shuffle[d + (q%c) & 7][q + (a%b) & 7],
            shuffle[a + (q%d) & 7][q + (b%c) & 7],
        ]

    output = [0] * len(input)
    for p, x in enumerate(input):
        output[p] = x ^ (a^b^c^d)

        a, b, c, d = [
            shuffle[b + (x%a) & 7][x + (c%d) & 7],
            shuffle[c + (x%b) & 7][x + (d%a) & 7],
            shuffle[d + (x%c) & 7][x + (a%b) & 7],
            shuffle[a + (x%d) & 7][x + (b%c) & 7],
        ]

    return output


def crypto_curse(input, key, shuffle):

    a, b, c, d = (1, 3, 5, 7)

    for q in key:
        q = ord(q)
        a, b, c, d = [
            shuffle[b + (q%a) & 7][q + (c%d) & 7],
            shuffle[c + (q%b) & 7][q + (d%a) & 7],
            shuffle[d + (q%c) & 7][q + (a%b) & 7],
            shuffle[a + (q%d) & 7][q + (b%c) & 7],
        ]

    output = [0] * (len(input) + 4)
    for p, x in enumerate(input):
        x = output[p] = x ^ (a^b^c^d)

        a, b, c, d = [
            shuffle[b + (x%a) & 7][x + (c%d) & 7],
            shuffle[c + (x%b) & 7][x + (d%a) & 7],
            shuffle[d + (x%c) & 7][x + (a%b) & 7],
            shuffle[a + (x%d) & 7][x + (b%c) & 7],
        ]

    for p in range(len(input), len(input)+4):
        x = output[p] = a ^ b ^ c ^ d ^ 0x43;

        a, b, c, d = [
            shuffle[b + (x%a) & 7][x + (c%d) & 7],
            shuffle[c + (x%b) & 7][x + (d%a) & 7],
            shuffle[d + (x%c) & 7][x + (a%b) & 7],
            shuffle[a + (x%d) & 7][x + (b%c) & 7],
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
