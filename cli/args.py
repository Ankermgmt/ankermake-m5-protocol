import argparse

from argparse import ArgumentParser, HelpFormatter, _SubParsersAction

def parse_init():
    parser = argparse.ArgumentParser()

    sub = parser.add_subparsers(required=True, title="subcommands", description=None, dest="mode", help=None)

    ## mqtt subcommand
    mqtt = sub.add_parser("mqtt", help="Low-level mqtt api access")
    mg0 = mqtt.add_argument_group("mqtt mode", "desc")
    mg = mg0.add_mutually_exclusive_group(required=True)
    mg.add_argument("-M", "--monitor", action="store_true", help="Monitor raw mqtt traffic")
    mg.add_argument("-S", "--status",  action="store_true", help="")

    ## pppp subcommand
    pppp = sub.add_parser("pppp", help="Low-level pppp api access")
    pp0 = pppp.add_argument_group("pppp mode", "desc")
    pp = pp0.add_mutually_exclusive_group(required=True)
    pp.add_argument("-M", "--monitor", action="store_true", help="Monitor raw pppp traffic")
    pp.add_argument("-S", "--lan-search", action="store_true", help="Search for locally available devices")

    http = sub.add_parser("http", help="Low-level http api access")

    ## config subcommand
    config = sub.add_parser("config", help="Manage settings and login details")
    configsub = config.add_subparsers(required=True)

    ## import subcommand
    impsub  = configsub.add_parser("import", help="import printer access details")
    imp = impsub.add_mutually_exclusive_group(required=True)
    imp.add_argument("-t", "--token", metavar="<auth-token>", help="Authorization token ")
    imp.add_argument("-f", "--file", action="store_true", help="Authorization token ")
    imp.add_argument("-a", "--auto", action="store_true", help="Authorization token ")

    return parser

def parse_args():
    return parse_init().parse_args()
