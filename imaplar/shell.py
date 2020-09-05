"""
Imaplar is a program which monitors mailboxes on IMAP servers for
incoming messages. When a message arrives, it is passed to a policy which
decides how it should be handled.
"""

import argparse
import cerberus
import collections.abc
import functools
import logging.config
import os
import ssl
import sys
import threading
import yaml
from . import imap
from . import schema

try:
    from importlib import metadata
except ImportError:
    import importlib_metadata as metadata

class ConfigurationError(Exception):
    pass

tls_modes = {
    "disabled": imap.TLSMode.DISABLED,
    "enabled": imap.TLSMode.ENABLED,
    "starttls": imap.TLSMode.STARTTLS,
}

ssl_verify_modes = {
    "none": ssl.CERT_NONE,
    "optional": ssl.CERT_OPTIONAL,
    "required": ssl.CERT_REQUIRED
}

auth_factories = {
    "login": lambda config: imap.LoginAuthenticator(
                    config["login_username"],
                    config["login_password"]),
    "plain": lambda config: imap.PlainAuthenticator(
                    config["plain_identity"],
                    config["plain_password"],
                    config["plain_authorization_identity"]),
    "oauth2": lambda config: imap.OAuth2Authenticator(
                    config["oauth2_user"],
                    config["oauth2_access_token"],
                    config["oauth2_mech"],
                    config["oauth2_vendor"])
}

def main(argv = sys.argv):
    # parse command line
    parser = argparse.ArgumentParser(prog = argv[0],
        description = __doc__)
    parser.add_argument("--config",
        default = os.path.expanduser("~/.imaplar"),
        help = "configuration file (default: '~/.imaplar')")
    parser.add_argument("--version", action = "version",
        version = metadata.version("imaplar"))
    parser.add_argument("servers", metavar = "server", nargs="*",
        help = "IMAP server")
    args = parser.parse_args(args = argv[1:])

    # read configuration
    validator = cerberus.Validator(schema.config)
    with open(args.config) as stream:
        config = validator.validated(yaml.load(stream))
    if not config:
        raise ConfigurationError(validator.errors)

    # configure logging
    if "logging" in config:
        logging.config.dictConfig(config["logging"])

    # compile policies
    policies = dict(
        (name, compile(code, "<policy_{}>".format(name), "exec"))
            for name, code in config["policies"].items())

    # monitored servers
    servers = args.servers if args.servers\
        else [k for k, v in config["servers"].items() if v["default"]]

    # configure sessions 
    sessions = []
    for server in servers:
        # server configuration
        server_config = config["servers"].get(server, None)
        if not server_config:
            raise ConfigurationError("{}: unknown server".format(server))

        # tls configuration
        tls_mode = imap.TLSMode.ENABLED
        ssl_context = None
        tls_config = server_config.get("tls", None)
        if tls_config:
            tls_mode = tls_modes[tls_config["mode"]]
            if tls_mode != imap.TLSMode.DISABLED:
                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)

                verify_mode = tls_config.get("verify_mode", None)
                if verify_mode:
                    ssl_context.verify_mode = ssl_verify_modes[verify_mode]

                check_hostname = tls_config.get("check_hostname", None)
                if check_hostname:
                    ssl_context.check_hostname = check_hostname

                cafile = tls_config.get("cafile", None)
                capath = tls_config.get("capath", None)
                cadata = tls_config.get("cadata", None)
                if cafile or capath or cadata:
                    ssl_context.load_verify_locations(cafile, capath, cadata)

        # authentication configuration
        authenticator = None
        auth_config = server_config.get("authentication", None)
        if auth_config:
            authenticator = auth_factories[auth_config["method"]](auth_config)
        
        # port configuration
        port = server_config.get("port",
            993 if tls_mode == imap.TLSMode.ENABLED else 143)

        for mailbox, policy in server_config["mailboxes"].items():
            if policy not in policies:
                raise ConfigurationError(
                    "{}: policy not defined".format(policy))
            sessions.append(imap.Session(server, port,
                tls_mode, ssl_context, authenticator,
                server_config["poll"], server_config["idle"],
                mailbox, policies[policy]))

    # run sessions
    for session in sessions:
        thread = threading.Thread(target = session.run_forever)
        thread.start()

if __name__ == "__main__":
    main()
