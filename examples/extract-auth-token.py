#!/usr/bin/env python3

from libflagship.util import b64d
import libflagship.logincache
import json
import sys
import platform
import os
import getopt

def jankauto():
    userdir = os.getlogin()
    useros = platform.system()

    darfileloc = f'/Users/{userdir}/Library/Application Support/AnkerMake/AnkerMake_64bit_fp/login.json'
    winfileloc = os.path.join('C:\\Users\\') + f'{userdir}' + os.path.join('\\AppData\\Local\\Ankermake\\login.json')
    
    try:
        opts, args = getopt.getopt(sys.argv[1:],"haf:", ["help", "auto", "file="])
    except getopt.GetoptError:
      print ('extract-auth-token.py -a OR extract-auth-token.py -f <path-to-login.json>')
      sys.exit(2)

    for opt, arg in opts: 
        if opt == '-h':
            print ('extract-auth-token.py -a OR extract-auth-token.py -f <path-to-login.json> \nIf spaces are in file location remember to escape them with a backslash')
            exit(1)
        elif opt in ("-f", "--file"):
            data = open(arg).read()
            jsonj = json.loads(libflagship.logincache.decrypt(data))
            print(jsonj["data"]["auth_token"])
            exit(1)
        elif opt in ("-a", "--auto"):
            if useros == 'Darwin':
                data = open(f'{darfileloc}').read()
                jsonj = json.loads(libflagship.logincache.decrypt(data))
                print(jsonj["data"]["auth_token"])
                exit(1)
            elif useros == 'Windows':
                data = open(f'{winfileloc}').read()
                jsonj = json.loads(libflagship.logincache.decrypt(data))
                print(jsonj["data"]["auth_token"])
                exit(1)
        else:
            assert False, "unhandled option"

jankauto()