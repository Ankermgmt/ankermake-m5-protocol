#!/usr/bin/env python3

from libflagship.util import b64d
import libflagship.logincache
import json
import sys

if len(sys.argv) != 2:
    print(f"usage: {sys.argv[0]} <path/to/login.json>")
    exit(1)

data = open(sys.argv[1]).read()

json = json.loads(libflagship.logincache.decrypt(data))
print(json["data"]["auth_token"])
