import argparse
import configparser
import logging.config
import os
import pkg_resources
import sys
import threading
import imaplar

def main(argv = sys.argv):
    # parse command line
    parser = argparse.ArgumentParser(prog = argv[0],
        description = "IMAP Watcher")
    parser.add_argument("--config", action = "append")
    parser.add_argument("--version", action= "store_true")
    parser.add_argument("servers", metavar = "server", nargs="*")
    ns = parser.parse_args(args = argv[1:])

    # report version?
    if ns.version:
       print(pkg_resources.require("imaplar")[0].version)
       return

    # read configuration
    config = configparser.ConfigParser()
    if ns.config:
        for path in ns.config:
            with open(path) as f:
                config.readfp(f)
    else:
        config.read([
            os.path.expanduser("~/.imaplar"),
            os.path.expanduser("~/.imaplar.cfg"),
            ".imaplar", ".imaplar.cfg"])

    # configure logging
    logging.config.fileConfig(config)

    # start monitoring threads
    sections = ns.servers if ns.servers else ["server"]
    for section in sections:
        monitor = imaplar.Monitor(config, section)
        thread = threading.Thread(target = monitor)
        thread.start()

if __name__ == "__main__":
    main()
