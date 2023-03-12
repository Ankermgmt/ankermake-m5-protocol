#!/usr/bin/env python3

import libflagship.pppp as pppp
from rich import print

# binary message to parse
input = b'\xf1C\x00,EUPRAKM\x00\x00\x0009ABCDE\x00\x00\x00\x00\x02iz(\x1e\x14\n\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
print(f"input:   {input}")

# parsing a message into structured data
msg, tail = pppp.Message.parse(input)
print(f"decoded: {msg}")

# packing a structured message into binary output
output = msg.pack()
print(f"encoded: {output}")

# the output must match our original input
assert input == output
