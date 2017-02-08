"""
Imaplar is a program which monitors email folders on IMAP servers for
incoming messages. When a message arrives, it is passed to a policy which
decides how it should be handled.
"""

import backports.ssl
import email.parser
import imapclient
import importlib
import logging
import time
import traceback
from . import policy
from . import util

class Monitor:
    """
    Folder monitor.
    """

    def __init__(self, config, section):
        # imap server configuration
        self._host = config.get(section, "host", fallback = "localhost")
        self._port = config.getint(section, "port", fallback = None)
        self._stream = config.getboolean(section, "stream", fallback = False)
        self._timeout = config.getint(section, "timeout", fallback = None)
        self._debug = config.getint(section, "debug", fallback = 0)

        # TLS configuration
        self._ssl = config.getboolean(section, "ssl", fallback = False)
        self._starttls = config.getboolean(section, "starttls", fallback = True)
        if self._ssl or self._starttls:
            self._context = imapclient.tls.create_default_context(
                config.get(section, "ssl_cafile", fallback = None),
                config.get(section, "ssl_capath", fallback = None),
                config.get(section, "ssl_cadata", fallback = None))
            self._context.check_hostname = config.getboolean(section,
                "ssl_check_hostname", fallback = True)
            if config.getboolean(section, "tls_cert_required", fallback = True):
                self._context.verify_mode = backports.ssl.CERT_REQUIRED
            else:
                self._context.verify_mode = backports.ssl.CERT_NONE

        # authentication configuration
        authenticate = config.get(section, "authenticate", fallback = None)
        if authenticate is None:
            self._authenticate = lambda client: None
            pass
        elif authenticate == "login":
            self._authenticate = lambda client: client.login(
                config.get(section, "login_username"),
                config.get(section, "login_password"))
        elif authentication == "oauth":
            self._authenticate = lambda client: client.oauth_login(
                config.get(section, "oauth_url"),
                config.get(section, "oauth_token"),
                config.get(section, "oauth_token_secret"),
                config.get(section, "oauth_consumer_key",
                    fallback = "anonymous"),
                config.get(section, "oauth_consumer_secret",
                    fallback = "anonymous"))
        elif authentication == "oauth2":
            self._authenticate = lambda client: client.oauth2_login(
                config.get(section, "oauth2_user"),
                config.get(section, "oauth2_token"),
                config.get(section, "oauth2_mech", fallback = "XOAUTH2"),
                config.get(section, "oauth2_vendor", fallback = None))
        else:
            raise Exception("{}: unknown authentication".format(authenticate))

        # monitored folder
        self._folder = config.get(section, "folder", fallback = "INBOX")
        self._query = config.get(section, "query", fallback = "UNSEEN")
        self._poll = config.getint(section, "poll", fallback = 0)

        # email policy
        self._policy = util.plugin(config,
            config.get(section, "policy", fallback = "policy"),
            policy.Null)

        # session retstart delay
        self._restart_delay = config.getint(section, "restart_delay",
            fallback = 300)

    def __call__(self):
        delay = 1
        while True:
            try:
                self._session()
            except:
                logging.error("session aborted: {}".format(
                    traceback.format_exc()))
                logging.error("restarting in {} seconds".format(
                    self._restart_delay))
                time.sleep(self._restart_delay)

    def _session(self):
        # connect to server
        logging.debug("connecting to {}{}{}".format(
            self._host,
            ":{}".format(self._port) if self._port else "",
            "[ssl]" if self._ssl else ""))
        client = IMAPClientWrapper(self._host,
            port = self._port,
            ssl = self._ssl,
            ssl_context = self._context,
            stream = self._stream,
            timeout = self._timeout)
        client.client.debug = self._debug

        # start TLS?
        if not self._ssl and self._starttls:
            if client.has_capability("STARTTLS"):
                logging.debug("start TLS")
                client.starttls(self._context)
            else:
                raise Exception("server doesn't support STARTTLS")

        # authenticate
        self._authenticate(client)

        # initial processing
        client.select_folder(self._folder, readonly = True)
        uids = client.search(self._query)
        for uid in uids:
            self._policy(client, self._folder, uid)

        if self._poll > 0:
            wait = lambda client: self._poll_wait(client, self._poll)
        elif client.has_capability("IDLE"):
            wait = self._idle_wait
        else:
            wait = lambda client: self._poll_wait(client, 60)

        uids = client.search("*")
        nextuid = uids[-1] if uids else 1
        while True:
            client.select_folder(self._folder, readonly = True)
            wait(client)
            uids = client.search("{}:* UNSEEN".format(nextuid))
            for uid in uids:
                self._policy(client, self._folder, uid)
            nextuid = uids[-1] if uids else nextuid

    def _poll_wait(self, client, period):
        while True:
            time.sleep(period)
            status, responses = client.noop()
            if any([x for x in responses if x[-1] == b"EXISTS"]):
                break

    def _idle_wait(self, client):
        client.idle()
        while True:
            responses = client.idle_check()
            if any([x for x in responses if x[-1] == b"EXISTS"]):
                client.idle_done()
                break

class IMAPClientWrapper:
    def __init__(self, *args, **kwargs):
        self._client = imapclient.IMAPClient(*args, **kwargs)

    def __getattr__(self, attr):
        return getattr(self._client, attr)

    @property
    def client(self):
        return self._client

    def fetch_messages(self, messages, modifiers = None, headersonly = False):
        data = ["BODY.PEEK[HEADER]" if headersonly else "BODY.PEEK[]"]
        response = self._client.fetch(messages, data, modifiers)

        parser = email.parser.BytesParser()
        data = b"BODY[HEADER]" if headersonly else b"BODY[]"
        items = [(key, parser.parsebytes(response[key][data], headersonly))
            for key in response]
        return dict(items)

    def fetch_headers(self, messages, modifiers = None):
        return self.fetch_messages(messages, modifiers, True)

    def glob_folders(self, patterns):
        folders = []
        for pattern in patterns:
            if "*" in pattern or "%" in pattern:
                for flags, delimiter, name in self._client.list_folders(
                        pattern = pattern):
                    folders.append(name)
            else:
                folders.append(pattern)
        return folders
         
    def move(self, messages, folder):
        self._client.copy(messages, folder)
        self._client.delete_messages(messages)
