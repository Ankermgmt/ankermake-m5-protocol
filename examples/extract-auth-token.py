#!/usr/bin/env python3

import sys             # nopep8
sys.path.append("..")  # nopep8

from libflagship.util import b64d
import libflagship.logincache

from os import path
import json
import platform
import argparse

def print_login(fd):
    jsonj = libflagship.logincache.load(fd.read())
    print(jsonj["data"]["auth_token"])

def parse_args():
    def fmt(prog):
        return argparse.HelpFormatter(prog,max_help_position=42)

    parser = argparse.ArgumentParser(
        prog="extract-auth-token",
        description="Extract auth token from ankermake slicer login.json",
        formatter_class=fmt
    )

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "-a", "--auto",
        action="store_true",
        help="Attempt auto-detection of login.json location"
    )

    group.add_argument(
        "-f", "--file",
        type=argparse.FileType("r"),
        metavar="<file>",
        help="Specify location of login.json"
    )

    return parser.parse_args()

def main():
    useros = platform.system()

    darfileloc = path.expanduser('~/Library/Application Support/AnkerMake/AnkerMake_64bit_fp/login.json')
    winfilelocs = [
        path.expandvars(r'%APPDATA%\Roaming\eufyMake Studio Profile\cache\offline\user_info'),
        path.expandvars(r'%APPDATA%\eufyMake Studio Profile\cache\offline\user_info'),
        path.expandvars(r'%LOCALAPPDATA%\Ankermake\AnkerMake_64bit_fp\login.json'),
    ]

    args = parse_args()

    if args.auto:

        if useros == 'Darwin':
            print_login(open(darfileloc))
        elif useros == 'Windows':
            for winfileloc in winfilelocs:
                if path.isfile(winfileloc):
                    print_login(open(winfileloc))
                    break
            else:
                exit("Could not find login.json/user_info on Windows; specify -f <filename>")
        else:
            exit("This platform does not support autodetection. Please specify file location with -f <filename>")

    elif args.file:
        print_login(args.file)

if __name__ == "__main__":
    exit(main())
