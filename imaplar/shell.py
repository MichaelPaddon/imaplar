import argparse
import configparser
import logging.config
import os
import sys
import threading
from . import client
from . import version

def main(argv = sys.argv):
    # parse command line
    parser = argparse.ArgumentParser(prog = argv[0],
        description = "IMAP mailbox monitor ({})".format(version.version))
    parser.add_argument("--config", action = "append")
    parser.add_argument("servers", metavar = "server", nargs="*")
    args = parser.parse_args(args = argv[1:])

    # read configuration
    config = configparser.ConfigParser()
    if args.config:
        for path in args.config:
            with open(path) as f:
                config.readfp(f)
    else:
        config.read([
            os.path.expanduser("~/.imaplar"),
            os.path.expanduser("~/.imaplar.cfg"),
            ".imaplar",
            ".imaplar.cfg"])

    # configure logging
    logging.config.fileConfig(config)

    # configure sessions
    sessions = []
    servers = args.servers if args.servers else ["server"]
    for server in servers:
        sessions.extend(client.Session.configure(config, server))

    # run sessions
    for session in sessions:
        thread = threading.Thread(target = session.run)
        thread.start()

if __name__ == "__main__":
    main()
