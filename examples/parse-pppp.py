#!/usr/bin/env python3

import sys
sys.path.append("..")

import libflagship.pppp as pppp
from libflagship.util import unhex

from rich import print

if len(sys.argv) < 2:
    print(f"usage: {sys.argv[0]} <hex string> ...")
    exit()

for hexinput in sys.argv[1:]:
    # binary message to parse
    input = unhex(hexinput)
    print(f"input:   {input}")

    # parsing a message into structured data
    msg, tail = pppp.Message.parse(input)
    print(f"decoded: {msg}")

    # packing a structured message into binary output
    output = msg.pack()
    print(f"encoded: {output}")

    # the output must match our original input
    assert input == output
