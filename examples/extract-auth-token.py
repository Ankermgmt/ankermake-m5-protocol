#!/usr/bin/env python3

from libflagship.util import b64d
import libflagship.logincache
import json
import sys
import platform
import os

userdir = os.getlogin()
useros = platform.system()

#darfileloc = f'/Users/{userdir}/Library/Application Support/AnkerMake/AnkerMake_64bit_fp/login.json'
darfileloc = f'/Users/thomaspatterson/Library/Application Support/AnkerMake/AnkerMake_64bit_fp/login.json'
winfileloc = os.path.join('C:\\Users\\') + f'{userdir}' + os.path.join('\\AppData\\Local\\Ankermake\\login.json')

if useros == 'Darwin':
    data = open(f'{darfileloc}').read()
    json = json.loads(libflagship.logincache.decrypt(data))
    print(json["data"]["auth_token"])
    exit(1)
elif useros == 'Windows':
    data = open(f'{winfileloc}').read()
    json = json.loads(libflagship.logincache.decrypt(data))
    print(json["data"]["auth_token"])
    exit(1)
elif len(sys.argv) != 2:
    print(f"usage: {sys.argv[0]} <path/to/login.json>")
    data = open(sys.argv[1]).read()
    json = json.loads(libflagship.logincache.decrypt(data))
    print(json["data"]["auth_token"])
    exit(1)
