#!/usr/bin/env python3

import hashlib
import random
from libflagship.util import enhex


# old v1 "check code"

def calc_check_code(sn, mac):
    input = f"{sn}+{sn[-4:]}+{mac}"
    return hashlib.md5(input.encode()).hexdigest()


# new v2 "security code"

def cal_hw_id_suffix(val):
    return sum((
        int(chr(val[-1]), 16),
        int(chr(val[-2]), 16),
        int(chr(val[-3]), 16),
        int(chr(val[-4]), 16),
    ))


def gen_base_code(sn, mac):
    last_digit = int(chr(sn[-1]), 16)

    offset = (last_digit + 10) % 10

    return sn[offset:] + str(cal_hw_id_suffix(mac)).encode()


def gen_check_code_v1(base_code, seed):
    base = b"01" + base_code + seed

    sha = hashlib.sha256(base).digest()

    str = bytearray(sha + sha[10:12])

    if (str[32] < 0x7d) or (str[33] < 0x7d):
        str[32] = (str[32] + str[33]) & 0xFF

    for x in range(0, 32, 2):
        if (str[x] < 0x7d) or (str[x+1] < 0x7d):
            str[x] = (str[x] + str[x+1]) & 0xFF

        if max(0x7d, str[x+1]) < str[x+2]:
            str[x+1] = str[x+2] - str[x+1]

        if (str[x+1] > 0x7d) and (str[x+1] > str[x+2]):
            str[x+1] = str[x+1] - str[x+2]

    return enhex(str[0x10:0x20]).upper()


def gen_rand_seed(mac):
    rnd = random.randint(10000000,99999999)

    suffix = cal_hw_id_suffix(mac)
    txtbuf = str(1000 - suffix) + str(rnd)

    sec_ts = "01%d" % rnd
    sec_code = hashlib.md5(txtbuf.encode()).hexdigest().upper().encode()

    return sec_ts, sec_code


def create_check_code_v1(sn, mac):
    base_code = gen_base_code(sn, mac)
    sec_ts, seed = gen_rand_seed(mac)
    sec_code = gen_check_code_v1(base_code, seed)
    return sec_ts, sec_code
