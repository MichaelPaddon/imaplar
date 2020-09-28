#
# Copyright (C) 2017-2020 Michael Paddon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Imaplar monitors one or more mailboxes on one or more IMAP servers.
Unseen messages are passed to a user defined policy for processing.
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
from . import client
from . import schema

try:
    from importlib import metadata
except ImportError:
    import importlib_metadata as metadata

class ConfigurationError(Exception):
    pass

tls_modes = {
    "disabled": client.TLSMode.DISABLED,
    "enabled": client.TLSMode.ENABLED,
    "starttls": client.TLSMode.STARTTLS,
}

ssl_verify_modes = {
    "none": ssl.CERT_NONE,
    "optional": ssl.CERT_OPTIONAL,
    "required": ssl.CERT_REQUIRED
}

auth_factories = {
    "login": lambda config: client.LoginAuthenticator(
                    config["login_username"],
                    config["login_password"]),
    "plain": lambda config: client.PlainAuthenticator(
                    config["plain_identity"],
                    config["plain_password"],
                    config["plain_authorization_identity"]),
    "oauth2": lambda config: client.OAuth2Authenticator(
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
        tls_mode = client.TLSMode.ENABLED
        ssl_context = None
        tls_config = server_config.get("tls", None)
        if tls_config:
            tls_mode = tls_modes[tls_config["mode"]]
            if tls_mode != client.TLSMode.DISABLED:
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
            993 if tls_mode == client.TLSMode.ENABLED else 143)

        # server specific parameters
        parameters = server_config.get("parameters", {})

        for mailbox, policy in server_config["mailboxes"].items():
            if policy not in policies:
                raise ConfigurationError(
                    "{}: policy not defined".format(policy))
            sessions.append(client.Session(server, port,
                tls_mode, ssl_context, authenticator,
                server_config["poll"], server_config["idle"],
                mailbox, policies[policy], parameters))

    # run sessions
    for session in sessions:
        thread = threading.Thread(target = session.run_forever, kwargs = {
           "min": server_config["min_backoff"],
           "max": server_config["max_backoff"]})
        thread.start()

if __name__ == "__main__":
    main()
