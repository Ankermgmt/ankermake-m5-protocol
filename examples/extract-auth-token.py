#!/usr/bin/env python3

from libflagship.util import b64d
import libflagship.logincache
import json
import sys
import platform
import os
import getopt

def print_login(filename):
    data = open(filename).read()
    jsonj = json.loads(libflagship.logincache.decrypt(data))
    print(jsonj["data"]["auth_token"])

def main():
    userdir = os.getlogin()
    useros = platform.system()

    darfileloc = f'/Users/{userdir}/Library/Application Support/AnkerMake/AnkerMake_64bit_fp/login.json'
    winfileloc = os.path.expandvars(r'%APPDATA%\Local\Ankermake\login.json')
    
    try:
        opts, args = getopt.getopt(sys.argv[1:],"haf:", ["help", "auto", "file="])
    except getopt.GetoptError:
      print ('extract-auth-token.py -a OR extract-auth-token.py -f <path-to-login.json>')
      return 2

    for opt, arg in opts: 
        if opt == '-h':
            print ('extract-auth-token.py -a OR extract-auth-token.py -f <path-to-login.json> \nIf spaces are in file location remember to escape them with a backslash')
            return(1)
        elif opt in ("-f", "--file"):
            print_login(arg)
        elif opt in ("-a", "--auto"):
            if useros == 'Darwin':
                print_login({darfileloc})
            elif useros == 'Windows':
                print_login({winfileloc})
        else:
            print ("extract-auth-token.py -a OR extract-auth-token.py -f <path-to-login.json>")
            return 1

if __name__ == "__main__":
    exit(main())